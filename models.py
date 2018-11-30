# encoding: utf-8
from app.external import db
from datetime import datetime


# 会员
class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True)
    pwd = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(11), unique=True)
    info = db.Column(db.Text)
    face = db.Column(db.String(255), unique=True)
    uuid = db.Column(db.String(255), unique=True)
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())
    userlogs = db.relationship('Userlog', backref='user')
    comments = db.relationship('Comment', backref='user')
    moviecols = db.relationship('Moviecol', backref='user')

    def __repr__(self):
        return '<User %r>'% self.name

    # 检查密码
    def check_pwd(self, pwd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


# 会员登录日志
class Userlog(db.Model):

    __tablename__ = 'userlog'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip = db.Column(db.String(100))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())


    def __repr__(self):
        return '<Userlog %r>' % self.id


# 标签
class Tag(db.Model):

    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True)
    movies = db.relationship("Movie", backref='tag')  # 电影外键关系关联
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Tag %r>'% self.name


# 电影
class Movie(db.Model):

    __tablename__ = 'movie'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), unique=True)
    url = db.Column(db.String(255), unique=True)
    info = db.Column(db.Text)
    logo = db.Column(db.String(255), unique=True)
    star = db.Column(db.SmallInteger)
    tag_id =db.Column(db.Integer, db.ForeignKey('tag.id'))
    playnum = db.Column(db.BigInteger)
    commentnum = db.Column(db.BigInteger)
    length = db.Column(db.String(100))
    area = db.Column(db.String(255))
    release_time = db.Column(db.Date) # 发布时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())
    comments =db.relationship('Comment', backref ='movie')
    moviecols = db.relationship('Moviecol', backref ='movie')


    def __repr__(self):
        return '<Movie %r>' % self.title


# 电影预告
class Previes(db.Model):

    __tablename__ = 'preview'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), unique=True)
    logo = db.Column(db.String(255), unique=True)
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Preview %r>' % self.title


# 评论
class Comment(db.Model):

    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.String(255), unique=True)  # 应该用Text， unique为保持数据的一致性要求掉
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Comment %r>' % self.id


# 收藏电影
class Moviecol(db.Model):

    __tablename__ = 'moviecol'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Moviecol %r>' % self.id


# 权限
class Auth(db.Model):

    __tablename__ = 'auth'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True)
    url = db.Column(db.String(255), unique=True)
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Auth %r>' % self.name


# 角色
class Role(db.Model):

    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True)
    auths = db.Column(db.String(600))
    admins = db.relationship('Admin', backref='role')
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Role %r>' % self.name


# 管理员
class Admin(db.Model):

    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True)
    pwd = db.Column(db.String(100), unique=True)
    is_super = db.Column(db.SmallInteger)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    adminlogs = db.relationship("Adminlog", backref='admin')  # Administrator login record foreign key
    oplogs = db.relationship("Oplog", backref='admin')  # administrator login foreign key

    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Admin %r>' % self.name

    def check_pwd(self, pwd):
        from werkzeug.security import check_password_hash

        return check_password_hash(self.pwd, pwd)


# 管理员登录
class Adminlog(db.Model):

    __tablename__ = 'adminlog'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    ip = db.Column(db.String(100))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Adminlog %r>' % self.id


# 管理员操作日志
class Oplog(db.Model):
    __tablename__ = 'oplog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    ip = db.Column(db.String(100))
    reason = db.Column(db.String(600)) # 操作原因
    addtime = db.Column(db.DateTime, index=True, default=datetime.now())

    def __repr__(self):
        return '<Oplog %r>' % self.id