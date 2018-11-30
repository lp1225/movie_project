# encoding: utf-8
# 调用蓝图
from . import home
from flask import render_template, redirect, url_for, flash, session, request
from functools import wraps
from werkzeug.utils import secure_filename
from form import RegisterForm, LoginForm, UserdetailForm, PwdForm, CommentForm
from models import User, Userlog, Previes, Tag, Movie, Comment, Moviecol
from app.external import db, app
import uuid, os, datetime, time, json
from app import qiniusdk


# 保存到七牛
def save_toqiniu(data, file , filename):
    filename = secure_filename(filename)
    filename = change_filename(filename)
    data = qiniusdk.qiniu_upload_file(file, filename)
    return data


# 修改文件名
def change_filename(filename):
    file_ext = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S")+str(uuid.uuid4().hex)+file_ext[-1]
    return filename


@home.route('/')
def home_index():
    return redirect(url_for('home.index',page=1))


# 首页电影筛选
@home.route('/<int:page>/', methods=['get'])
def index(page=None):
    if page == None:
        page = 1
    tag = Tag.query.all()
    movie = Movie.query
    # 标签筛选分页
    tid = request.args.get('tid', '0')
    if int(tid) != 0:
        movie = movie.filter_by(tag_id=int(tid))
    # 星级
    star = request.args.get('star', '0')
    if int(star) != 0:
        movie = movie.filter_by(star=int(star))
    # 时间
    time = request.args.get('time', '0')
    if int(time) != 0:
        if int(time) == 1:
            movie = movie.order_by(Movie.addtime.desc())
        else:
            movie = movie.order_by(Movie.addtime.asc())
    # 播放量
    pm = request.args.get('pm', '0')
    if int(pm) != 0:
        if int(pm) == 1:
            movie = movie.order_by(Movie.playnum.desc())
        else:
            movie = movie.order_by(Movie.playnum.asc())
    # 评论数
    cm = request.args.get('cm', '0')
    if int(cm) != 0:
        if int(cm) == 1:
            movie = movie.order_by(Movie.commentnum.desc())
        else:
            movie = movie.order_by(Movie.commentnum.asc())

    movie = movie.paginate(page=page, per_page=12)
    # 将获取到的参数保存在一个dict
    p = dict(
        tid=tid, star=star, time=time, pm=pm, cm=cm
    )

    return render_template('home/index.html', p=p, tag=tag, movie=movie)


# 访问控制
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('home.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# 会员登录
@home.route('/login/', methods=['get', 'post'])
def login():
    if 'user' in session:
        return redirect(url_for('home.user'))
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data

        if User.query.filter_by(name=data['name']).count() == 0:
            flash('账号不存在', 'err')
            return redirect(url_for('home.login'))
        user = User.query.filter_by(name=data['name']).first()
        # if not user.check_pwd(data['pwd']):
        # 验证密码
        from werkzeug.security import check_password_hash
        if not check_password_hash(user.pwd, data['pwd']):
            flash('密码不正确', 'err')

            return redirect(url_for('home.login'))

        session['user'] = user.name
        session['user_id'] = user.id
        userlog = Userlog(
            user_id=user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for('home.user'))

    return render_template('home/login.html', form=form)


@home.route('/logout/')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)

    return redirect(url_for('home.index', page=1))


# 会员注册
@home.route('/register/', methods=['get', 'post'])
def register():
    form = RegisterForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        user = User(
                name = data['name'],
                email = data['email'],
                phone = data['phone'],
                pwd = generate_password_hash(data['pwd']),
                uuid = uuid.uuid4().hex
            )
        db.session.add(user)
        db.session.commit()
        flash('会员注册成功,请登录', 'ok')
        return redirect(url_for('home.login'))

    return render_template('home/register.html', form=form)


# 会员中心
@home.route('/user/', methods=['get', 'post'])
@user_login_req
def user():
    form = UserdetailForm()
    user = User.query.get(int(session['user_id']))
    # 给表单数据
    form.face.validators = []
    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info

    if form.validate_on_submit():
        data = form.data
        if not os.path.exists(app.config['FC_DIR']):
            os.makedirs(app.config['FC_DIR'])
            os.chmod(app.config['FC_DIR'],  'rw')

        if form.face.data!='':
            # if user.face != None:
            #     if os.path.exists(app.config['FC_DIR'] + user.face):
            #         os.remove(app.config['FC_DIR'] + user.face)
            # file_face = secure_filename(form.face.data.filename)
            # filename = chang_filename(file_face)
            # #print 2,user.face
            # #print 3,form.face.data
            # form.face.data.save(app.config['FC_DIR']+ user.face)
            #----------------------------
            # user.face =qiniusdk.qiniu_upload_file(form.face.data,filename)
            # print user.face
            user.face = save_toqiniu(user.face, form.face.data, form.face.data.filename)
        # 验证
        name_count = User.query.filter_by(name=data["name"]).count()
        if data["name"] != user.name and name_count == 1:
            flash("账户名已存在!", "err")
            return redirect(url_for("home.user"))

        email_count = User.query.filter_by(email=data["email"]).count()
        if data["email"] != user.email and email_count == 1:
            flash("邮箱已存在!", "err")
            return redirect(url_for("home.user"))

        phone_count = User.query.filter_by(phone=data["phone"]).count()
        if data["phone"] != user.phone and phone_count == 1:
            flash("电话号已存在!", "err")
            return redirect(url_for("home.user"))

        user.name = data['name'],
        user.email = data['email'],
        user.phone = data['phone'],
        user.info = data['info']

        db.session.add(user)
        db.session.commit()
        flash('会员信息修改成功', 'ok')
        return redirect(url_for('home.user'))

    return render_template('home/user.html', form=form, user=user)


@home.route('/pwd/', methods=['get', 'post'])
@user_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.get(int(session['user_id']))
        from werkzeug.security import check_password_hash, generate_password_hash
        if not check_password_hash(user.pwd, data['old_pwd']):
            flash('旧密码错误，请重新输入', 'err')
            return redirect(url_for('home.pwd'))
        user.pwd = generate_password_hash(data['new_pwd'])
        db.session.commit()
        flash('密码修改成功请重新登录','ok')
        return redirect(url_for('home.login'))

    return render_template('home/pwd.html', form=form)


@home.route('/comments/<int:page>/', methods = ['get'])
@user_login_req
def comments(page=None):
    if page == None:
        page = 1
    comment = Comment.query.join(User).join(Movie).filter(
        User.id == session['user_id'],
        Movie.id == Comment.movie_id
    ).order_by(Comment.addtime.desc()).paginate(page=page, per_page=5)
    return render_template('home/comments.html', comment=comment)


# 登录日志
@home.route('/loginlog/<int:page>/', methods=['get'])
@user_login_req
def loginlog(page=None):
    if page == None:
        page = 1
    userlog = Userlog.query.filter_by(user_id=session['user_id']).order_by(Userlog.addtime.desc()).paginate(page=page, per_page=10)
    return render_template('home/loginlog.html', userlog=userlog)


# 添加电影收藏
@home.route("/moviecol/add/", methods=['get'])
@user_login_req
def moviecol_add():
    uid = request.args.get("uid", "")
    mid = request.args.get("mid", "")
    moviecol = Moviecol.query.filter_by(
        user_id=int(uid),
        movie_id=int(mid)
    ).count()
    if moviecol == 1:  # already been collected
        data = dict(ok=0)
    if moviecol == 0:
        moviecol = Moviecol(
            user_id=int(uid),
            movie_id=int(mid)
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)

    return json.dumps(data)


# 收藏电影处理
@home.route('/moviecol/<int:page>/', methods=['get'])
@user_login_req
def moviecol(page=None):
    if page == None:
        page = 1
    moviecol = Moviecol.query.join(Movie).filter(Moviecol.user_id == session['user_id'], Movie.id == Moviecol.movie_id).order_by(Moviecol.addtime.desc()).paginate(page=page, per_page=10)

    return render_template('home/moviecol.html', moviecol=moviecol)


@home.route('/animation/')
def animation():
    preview = Previes.query.all()
    return render_template('home/animation.html', preview=preview)


# 查询
@home.route('/search/<int:page>/', methods=['get'])
def search(page=None):
    if page == None:
        page = 1
    # 获取key
    key = request.args.get('key')
    # 模糊查询
    movie_count = Movie.query.filter(Movie.title.ilike('%' + key + '%')).count()
    if key != '' and movie_count != 0:
        if movie_count != 0:
            page_data = Movie.query.filter(
                Movie.title.ilike('%'+key+'%')
            ).order_by(Movie.addtime.desc()).paginate(page=page, per_page=5)
            page_data.key = key

            return render_template('home/search.html', key=key, page_data=page_data, movie_count=movie_count)
    else:
        page_data = None
        movie_count = 0
        key = key
        flash('未找到合适的电影', 'err')
        return render_template('home/search.html', key=key, page_data=page_data, movie_count=movie_count)


# 播放页面
@home.route("/play/<int:id>/<int:page>/", methods=['get', 'post'])
def play(id, page=None):
    if page == None:
        page = 1
    form = CommentForm()
    # movie =Movie.query.get(int(id))
    movie = Movie.query.join(Tag).filter(Tag.id == Movie.tag_id, Movie.id == int(id)).first()
    movie.playnum = movie.playnum + 1
    db.session.commit()
    # 分页查询
    page_data = Comment.query.join(User).join(Movie).filter(
        User.id == Comment.user_id, Movie.id == movie.id
    ).order_by(Comment.addtime.desc()).paginate(page=page, per_page=5)
    if 'user'in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data['content'],
            movie_id=movie.id,
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论添加成功','ok')
        movie.commentnum = movie.commentnum + 1
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('home.play', page=page, id=id))

    return render_template("home/play.html", movie=movie, form=form, page_data=page_data)
