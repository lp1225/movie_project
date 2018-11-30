#encoding: utf-8
#调用蓝图
from . import admin
from flask import render_template, redirect, url_for, flash, session, request, abort
from app.admin.form import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from models import Admin, Tag, Movie, Previes, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from functools import wraps
from app.external import db
from werkzeug.utils import secure_filename
import time, os, datetime, uuid
from app import app, qiniusdk



# @admin.route('/')
# def admin():
#     return '<h1 style="color:green">this is admin</h1>'


# 访问控制
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login',next = request.url))
        return f(*args, **kwargs)
    return decorated_function


# 访问权限控制
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = Admin.query.join(Role).filter(Role.id == Admin.role_id, Admin.id == session['admin_id']).first()
        print admin
        auths = admin.role.auths
        print auths
        # 转为int型
        auths = list(map(lambda v: int(v), auths.split(',')))
        auth_list = Auth.query.all()
        print auth_list
        urls =[v.url for v in auth_list for val in auths if val == v.id]
        print urls
        url = request.url_rule
        print url
        if str(url) not in urls:
            abort(404)
        return f(*args, **kwargs)
    return decorated_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S')+str(uuid.uuid4().hex)+fileinfo[-1]
    return filename


# 保存到七牛
def save_toqiniu(file , filename):
    filename = secure_filename(filename)
    filename = change_filename(filename)
    data = qiniusdk.qiniu_upload_file(file, filename)
    return data


# 上下文处理器
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    return data


@admin.route('/login/',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()

        if not admin.check_pwd(data['pwd']):
            flash('密码错误', 'login')
            return redirect(url_for('admin.login'))
        session['admin'] = data['account']
        session['admin_id'] = admin.id

        # 加入登录日志
        adminlog = Adminlog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html', form=form)


@admin.route('/logout/')
def logout():
    session.pop('admin', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))


@admin.route('/')
@admin_login_req
def index():
    return render_template('admin/index.html')


# 修改密码
@admin.route('/pwd/', methods=['get', 'post'])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session['admin']).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data['new_pwd'])
        db.session.commit()
        flash('修改密码成功,请重新登录','pwd')
        return redirect(url_for('admin.login'))
    return render_template('admin/pwd.html', form = form)


# 标签管理
@admin.route('/tag/add/', methods=['get', 'post'])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data

        tag_len = Tag.query.filter_by(name=form['name']).count()
        if tag_len !=0:
            flash('该标签已存在', 'err')
            return redirect(url_for('admin.tag_add'))
        else:
            tag = Tag(name=data['name'])
            db.session.add(tag)
            db.session.commit()
            flash('该标签添加成功', 'ok')
            # 操作日志
            oplog =Oplog(
                admin_id=session['admin_id'],
                ip=request.remote_addr,
                reason='添加了一个标签%s'% data['name']
            )
            db.session.add(oplog)
            db.session.commit()
            return redirect(url_for('admin.tag_add'))

    return render_template('admin/tag_add.html', form=form)


# 分页
@admin.route('/tag/list/<int:page>/', methods=['get'])
@admin_login_req
@admin_auth
def tag_list(page=None):
    if page == None:
        page = 1
    tag = Tag.query.order_by(Tag.addtime.desc()).paginate(page=page,per_page=5)
    return render_template('admin/tag_list.html', tag=tag)


@admin.route('/tag/del/<int:id>/', methods=['get'])
@admin_login_req
@admin_auth
def tag_del(id=None):
    tag = Tag.query.filter_by(id =id).first()
    print(tag)
    db.session.delete(tag)
    db.session.commit()
    flash('标签删除成功','ok')
    return redirect(url_for('admin.tag_list',page=1))


# 编辑标签
@admin.route('/tag/edit/<int:id>/',methods=['get', 'post'])
@admin_login_req
@admin_auth
def tag_edit(id=None):
    form = TagForm()
    if form.validate_on_submit():
        form = form.data
        tag = Tag.query.filter_by(id =id).first()
        tag_count = Tag.query.filter_by(name = form['name']).count()
        print tag.name
        print form['name']

        if tag.name == form['name'] or tag_count == 1:
            flash('该标签名称已存在','err')
            return redirect(url_for('admin.tag_edit',id=id))
        else:
            tag.name = form['name']
            db.session.commit()
            flash('改标签名称成功', 'ok')
            return redirect(url_for('admin.tag_list',page=1))
    return render_template('admin/tag_edit.html',form=form)


# 电影添加
@admin.route('/movie/add/', methods=['get', 'post'])
@admin_login_req
def movie_add():
    form=MovieForm()
    form.tag_id.choices = [(v.id, v.name) for v in Tag.query.all()]
    if form.validate_on_submit():
        data = form.data
        # 获取表单数据
        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 'rw')
        # #保存操作
        # url = change_filename(file_url)
        # form.url.data.save(app.config['UP_DIR']+url)
        # logo = change_filename(file_logo)
        # form.logo.data.save(app.config['UP_DIR'] + logo)

        # 保存到七牛云
        url_name = change_filename(file_url)
        logo_name = change_filename(file_logo)
        logo = qiniusdk.qiniu_upload_file(form.logo.data,logo_name)
        url = qiniusdk.qiniu_upload_file(form.url.data, url_name)
        print '-------------', url

        movie = Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            tag_id=int(data['tag_id']),
            playnum=0,
            commentnum=0,
            length=data['length'],
            area=data['area'],
            release_time=data['release_time']
        )
        db.session.add(movie)
        db.session.commit()
        flash('电影保存成功', 'ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


# 电影列表
@admin.route('/movie/list/<int:page>/', methods=['get'])
@admin_login_req
def movie_list(page=None):
    if page == None:
        page = 1
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=5)
    return render_template('admin/movie_list.html',movie=movie)


# 电影删除
@admin.route('/movie/del/<int:id>/', methods=['get'])
@admin_login_req
def movie_del(id=None):
    movie = Movie.query.get(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash('电影删除成功', 'ok')
    return redirect(url_for('admin.movie_list', page=1))


# 电影编辑
@admin.route('/movie/edit/<int:id>/', methods=['get','post'])
@admin_login_req
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators=[]
    form.logo.validators=[]
    movie = Movie.query.get(int(id))
    # 初始化
    form.tag_id.choices = [(v.id, v.name) for v in Tag.query.all()]
    if request.method == "GET":
        form.info.data = movie.info
        form.star.data = movie.star
        form.tag_id.data = movie.tag_id
    # 修改
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title =data['title']).count()
        if movie_count == 1 and movie.title != data['title']:
            flash('该标题已存在','err')
            return redirect(url_for('admin.movie_edit', id=id))

        # if not os.path.exists(app.config['UP_DIR']):
        #     os.makedirs(app.config['UP_DIR'])
        #     os.chmod(app.config['UP_DIR'],'rw')


        if form.url.data !='':
            # file_url = secure_filename(form.url.data.filename)
            # movie.url = change_filename(file_url)
            # form.url.data.save(app.config['UP_DIR'] + movie.url)
            movie.url = save_toqiniu(form.url.data, form.url.data.filename)

        if form.logo.data !='':
            # file_logo = secure_filename(form.logo.data.filename)
            # movie.logo = change_filename(file_logo)
            # form.logo.data.save(app.config['UP_DIR'] + movie.logo)
            movie.logo = save_toqiniu(form.logo.data, form.logo.data.filename)

        movie.title = data['title']
        movie.star = data['star']
        movie.tag_id = data['tag_id']
        movie.info = data['info']
        movie.area = data['area']
        movie.release_time = data['release_time']
        movie.length = data['length']
        db.session.add(movie)
        db.session.commit()
        flash('修改电影成功','ok')
        print data['info']
        print movie.info
        return redirect(url_for('admin.movie_edit',id = id))

    return render_template('admin/movie_edit.html',form=form,movie=movie)


# 添加电影预告
@admin.route('/preview/add/', methods=['get','post'])
@admin_login_req
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        # 保存文件
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 'rw')
        logo = change_filename(file_logo)
        form.logo.data.save(app.config['UP_DIR']+logo)
        preview = Previes(
            title=data['title'],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash('添加电影预告成功', 'ok')
        return redirect(url_for('admin.preview_add'))
    return render_template('admin/preview_add.html', form=form)


# 预告列表
@admin.route('/preview/list/<int:page>/')
@admin_login_req
def preview_list(page=None):
    if page == None:
        page = 1
    preview = Previes.query.order_by(Previes.addtime.desc()).paginate(page=page, per_page=2)
    return render_template('admin/preview_list.html', preview=preview)


@admin.route('/preview/del/<int:id>/')
@admin_login_req
def preview_del(id=None):
    preview = Previes.query.get(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash('预告删除成功','ok')

    return redirect(url_for('admin.preview_list',page=1))


# 预告编辑
@admin.route('/preview/edit/<int:id>/', methods=['get', 'post'])
@admin_login_req
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Previes.query.get(int(id))

    if form.validate_on_submit():
        data = form.data
        preview_count = Previes.query.filter_by(title=data['title']).count()
        if preview_count == 1 or preview.title == data['title']:
            flash('预告名已存在', 'err')
            return redirect(url_for('admin.preview_edit',id = id))
    # 文件处理
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 'rw')
        if form.logo.data !='':
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + preview.logo)

        preview.title = data['title'],
        db.session.add(preview)
        db.session.commit()
        flash('电影预告编辑成功','ok')

    return render_template('admin/preview_edit.html', form=form, preview=preview)


# 会员列表
@admin.route('/user/list/<int:page>/', methods=['get'])
@admin_login_req
def user_list(page=None):
    if page == None:
        page = 1
    user = User.query.order_by(User.addtime.desc()).paginate(page=page, per_page=10)
    return render_template('admin/user_list.html', user=user)


@admin.route('/user/del/<int:id>/',methods=['get', 'post'])
@admin_login_req
def user_del(id):
    # 删除本地文件
    user = User.query.get(int(id))
    # 文件若在云上则不需要
    # if user.face != None:
    #     # print app.config['FC_DIR']+user.face
    #     if os.path.exists(app.config['FC_DIR']+user.face):
    #         os.remove(app.config['FC_DIR']+user.face)
    db.session.delete(user)
    db.session.commit()

    flash('会员删除成功','ok')
    return redirect(url_for('admin.user_list',page=1))


# 会员详细信息查看
@admin.route('/user/view/<int:id>/', methods=['get', 'post'])
@admin_login_req
def user_view(id):
    user = User.query.get(int(id))

    return render_template('admin/user_view.html', user=user)


# 评论管理
@admin.route('/comment/list/<int:page>/', methods=['get'])
@admin_login_req
def comment_list(page =None):
    if page == None:
        page = 1
    comment = Comment.query.join(User).join(Movie).filter(User.id == Comment.user_id,Movie.id == Comment.movie_id).\
        order_by(Comment.addtime.desc()).paginate(page=page, per_page=5)

    return render_template('admin/comment_list.html', comment=comment)


@admin.route('/comment/del/<int:id>/', methods=['get'])
@admin_login_req
def comment_del(id):
    comment = Comment.query.get(int(id))
    comment.movie.commentnum -= 1
    db.session.delete(comment)
    db.session.commit()

    flash('评论删除成功','ok')
    return redirect(url_for('admin.comment_list', page=1))


# 收藏列表
@admin.route('/moviecol/list/<int:page>/',methods=['get'])
@admin_login_req
def moviecol_list(page=None):
    if page == None:
        page = 1
    moviecol = Moviecol.query.join(User).join(Movie).filter(User.id == Moviecol.user_id, Movie.id ==Moviecol.movie_id).\
        order_by(Moviecol.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('admin/moviecol_list.html', moviecol=moviecol)


@admin.route('/moviecol/del/<int:id>/', methods=['get'])
@admin_login_req
def moviecol_del(id):
    moviecol = Moviecol.query.get(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash('评论收藏成功','ok')
    return redirect(url_for('admin.moviecol_list', page=1))


# 日志操作
@admin.route('/oplog/list/<int:page>/', methods=['get'])
@admin_login_req
def oplog_list(page=None):
    if page == None:
        page = 1
    oplog = Oplog.query.join(Admin).filter(Admin.id == Oplog.admin_id).\
        order_by(Oplog.addtime.desc()).paginate(page=page, per_page=5)

    return render_template('admin/oplog_list.html', oplog=oplog)


@admin.route('/adminloginlog/list/<int:page>/', methods=['get'])
@admin_login_req
def adminloginlog_list(page=None):
    if page == None:
        page = 1
    adminlog = Adminlog.query.join(Admin).filter(Admin.id == Adminlog.admin_id).\
        order_by(Adminlog.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('admin/adminloginlog_list.html', adminlog=adminlog)


# 会员日志
@admin.route('/userloginlog/list/<int:page>/', methods=['get'])
@admin_login_req
def userloginlog_list(page = None):
    if page == None:
        page = 1
    userlog = Userlog.query.join(User).filter(User.id == Userlog.user_id).\
        order_by(Userlog.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('admin/userloginlog_list.html', userlog=userlog)


@admin.route('/role/add/', methods=['get', 'post'])
@admin_login_req
def role_add():
    form = RoleForm()
    form.auths.choices = [(v.id, v.name) for v in Auth.query.all()]
    if form.validate_on_submit():
        data = form.data
        print data['auths']
        role = Role(
            name=data['name'],
            auths=','.join(map(lambda v: str(v), data['auths']))
        )
        print role.auths
        db.session.add(role)
        db.session.commit()
        flash('添加角色成功','ok')
        return redirect(url_for('admin.role_add'))

    return render_template('admin/role_add.html', form=form)


# 角色删除，编辑
@admin.route('/role/del/<int:id>/', methods=['get'])
@admin_login_req
def role_del(id):
    role = Role.query.get(int(id))
    db.session.delete(role)
    db.session.commit()
    flash('角色删除成功','ok')
    return redirect(url_for('admin.role_list', page=1))


@admin.route('/role/edit/<int:id>/', methods=['get', 'post'])
@admin_login_req
def role_edit(id):
    form = RoleForm()
    form.auths.choices = [(v.id, v.name) for v in Auth.query.all()]

    role = Role.query.get(int(id))
    # 强调
    if request.method == "GET":
        auths = role.auths
        form.auths.data =list(map(lambda v : int(v), auths.split(',')))
    if form.validate_on_submit():
        data = form.data
        role.name = data['name']
        print data['auths']
        role.auths = ','.join(map(lambda v : str(v), data['auths']))
        print role.auths
        db.session.add(role)
        db.session.commit()
        flash('角色编辑成功','ok')

    return render_template('admin/role_edit.html', form=form, role=role)


@admin.route('/role/list/<int:page>/', methods=['get'])
@admin_login_req
def role_list(page=None):
    if page == None:
        page = 1
    role = Role.query.order_by(Role.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('admin/role_list.html', role=role)


# 权限管理
@admin.route('/auth/add/', methods=['get', 'post'])
@admin_login_req
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name = data['name'],
            url = data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash('权限添加成功', 'ok')
    return render_template('admin/auth_add.html', form=form)


@admin.route('/auth/list/<int:page>/', methods=['get'])
@admin_login_req
def auth_list(page=None):
    if page == None:
        page = 1
    auth = Auth.query.order_by(Auth.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('admin/auth_list.html', auth=auth)


@admin.route('/auth/del/<int:id>/',methods=['get'])
@admin_login_req
def auth_del(id=None):
    auth = Auth.query.filter_by(id =id).first()
    db.session.delete(auth)
    db.session.commit()
    flash('标签删除成功','ok')
    return redirect(url_for('admin.auth_list', page=1))


@admin.route("/auth/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get(int(id))
    if form.validate_on_submit():
        data = form.data
        auth.name = data["name"]
        auth.url = data["url"]
        db.session.add(auth)
        db.session.commit()
        flash("编辑成功!", "ok")
        redirect(url_for("admin.auth_edit", id=id))
    return render_template("admin/auth_edit.html", form=form, auth=auth)


# 管理员管理
@admin.route('/admin/add/', methods=['get', 'post'])
@admin_login_req
def admin_add():
    form = AdminForm()
    form.role_id.choices = [(v.id, v.name) for v in Role.query.all()]
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data['name'],
            pwd=generate_password_hash(data['pwd']),
            is_super=0,
            role_id=data['role_id']
        )
        db.session.add(admin)
        db.session.commit()
        flash('添加管理员成功', 'ok')

    return render_template('admin/admin_add.html', form=form)


@admin.route('/admin/list/<int:page>/', methods=['get'])
@admin_login_req
def admin_list(page=None):
    if page == None:
        page = 1
    admin = Admin.query.join(Role).filter(Role.id == Admin.role_id).order_by(Admin.addtime.desc()).paginate(page=page, per_page=5)

    return render_template('admin/admin_list.html', admin=admin)
