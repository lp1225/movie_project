# encoding: utf8
from app import app, db
from flask_script import Manager
from models import Role, Admin, Tag
from werkzeug.security import generate_password_hash

manager = Manager(app)


@manager.command
def init_database():
    # db.drop_all()
    # db.create_all()
    role = Role(name='超级管理员', auths='')
    db.session.add(role)
    db.session.commit()

    admin = Admin(name ='lp', pwd =generate_password_hash('lp'), is_super=0, role_id=1)
    db.session.add(admin)
    db.session.commit()
    # admin = Admin(name='aaa', pwd='1234', is_super=0, role_id=1)
    # db.session.add(admin)
    # db.session.commit()
    # tags = Tag.query.all()
    # print tags


if __name__ == '__main__':
    manager.run()
