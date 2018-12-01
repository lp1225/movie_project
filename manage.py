# encoding: utf8
from app import app, db
from flask_script import Manager
from models import Role, Admin, Tag, Movie
from werkzeug.security import generate_password_hash
from elasticsearch import Elasticsearch
import json


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


@manager.command
def create_index():
    """
    创建es索引
    """
    search_movie = Movie.query.all()
    movies = {}
    movie_list = []
    for m in search_movie:
        movies[str(m.id)] = {
                    'title': m.title,
                    'url': m.url,
                    'info': m.info,
                    'logo': m.logo,
                    'star': m.star,
                    'playnum': m.playnum,
                    'commentnum': m.commentnum,
        }
    for key, value in movies.items():
        movie_list.append(value)

    # movie_json = json.dumps(movies)
    # 往索引中插入数据
    es = Elasticsearch()
    for data in movie_list:
        result = es.index(index='movies', doc_type='video', body=data)
        print(result)


@manager.command
def cr_esindex():
    """
    建立索引
    :return:
    """
    es = Elasticsearch()
    result = es.indices.delete(index='movies', ignore=[400, 404])
    result = es.indices.create(index='movies', ignore=400)
    print(result)


@manager.command
def search_conf():
    """
    配置全文检索
    :return:
    """
    es = Elasticsearch()
    mapping = {
        'properties': {
            'title': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'search_analyzer': 'ik_max_word'
            }
        }
    }
    # 配置analysis-ik
    es.indices.delete(index='movies', ignore=[400, 404])
    es.indices.create(index='movies', ignore=400)
    result = es.indices.put_mapping(index='movies', doc_type='video', body=mapping)
    print(result)


@manager.command
def search_test():
    """
    查询测试
    :return:
    """
    es = Elasticsearch()
    dsl = {
        'query': {
            'match': {
                'title': '蜘蛛  侠'
            }
        }
    }
    result = es.search(index='movies', doc_type='video', body=dsl)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    manager.run()
