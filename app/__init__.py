#encoding: utf-8

from flask import render_template
from external import db,app
from admin import views
from home import views
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')


app.config['SECRET_KEY']=os.urandom(24)
app.config['UP_DIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/upload/')
app.config['FC_DIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/upload/users/')
app.debug=True
db.init_app(app)


from app.home import home as home_blueprint
from admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('home/404.html'),404

