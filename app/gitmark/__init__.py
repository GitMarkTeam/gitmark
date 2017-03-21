import os

from flask import Flask
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_principal import Principal 
from flask_mail import Mail
from flask_admin import Admin

from celery import Celery
from .config import config, Config


db = MongoEngine()

login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'accounts.login'

principals = Principal()
mail = Mail()
celery_app = Celery(__name__, broker=Config.BROKER_URL)


def init_admin(app):
    from model_admin import GeneralAdminIndexView, register_admin_views
    admin = Admin(app, name='GitMark Admin', index_view=GeneralAdminIndexView(url='/model-admin'))
    register_admin_views(admin)

# def create_app():
#     config_name = os.getenv('config') or 'default'
#     app = Flask(__name__, 
#         template_folder=config[config_name].TEMPLATE_PATH, static_folder=config[config_name].STATIC_PATH)
#     app.config.from_object(config[config_name])

#     config[config_name].init_app(app)

#     db.init_app(app)
#     login_manager.init_app(app)
#     principals.init_app(app)
#     mail.init_app(app)

#     init_admin(app)


#     return app

def register_blueprint(app):

    from main.urls import main as main_blueprint
    from accounts.urls import accounts as accounts_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(accounts_blueprint, url_prefix='/accounts')

    return app

def create_app():
    config_name = os.getenv('config') or 'default'
    app = Flask(__name__, 
        template_folder=config[config_name].TEMPLATE_PATH, static_folder=config[config_name].STATIC_PATH)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    principals.init_app(app)
    mail.init_app(app)

    init_admin(app)

    celery_app.conf.update(app.config)

    from main.urls import main as main_blueprint
    from accounts.urls import accounts as accounts_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(accounts_blueprint, url_prefix='/accounts')


    return app


# def make_celery(app):
#     celery = Celery(app.import_name, broker=app.config['BROKER_URL'])
#     celery.conf.update(app.config)
#     TaskBase = celery.Task
#     class ContextTask(TaskBase):
#         abstract = True
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return TaskBase.__call__(self, *args, **kwargs)
#     celery.Task = ContextTask
#     return celery

# app = create_app()
# celery_app = make_celery(app)