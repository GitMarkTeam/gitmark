import os

from flask import Flask
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_principal import Principal 

from celery import Celery
from config import config


db = MongoEngine()

login_manager = LoginManager()
# login_manager.session_protection = 'strong'
login_manager.session_protection = 'basic'
login_manager.login_view = 'accounts.login'

principals = Principal()


# def create_app():
#     config_name = os.getenv('config') or 'default'
#     app = Flask(__name__, 
#         template_folder=config[config_name].TEMPLATE_PATH, static_folder=config[config_name].STATIC_PATH)
#     app.config.from_object(config[config_name])

#     config[config_name].init_app(app)

#     db.init_app(app)
#     login_manager.init_app(app)
#     principals.init_app(app)

#     from main.urls import main as main_blueprint
#     from accounts.urls import accounts as accounts_blueprint

#     app.register_blueprint(main_blueprint)
#     app.register_blueprint(accounts_blueprint, url_prefix='/accounts')

#     return app

def create_app():
    config_name = os.getenv('config') or 'default'
    app = Flask(__name__, 
        template_folder=config[config_name].TEMPLATE_PATH, static_folder=config[config_name].STATIC_PATH)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    principals.init_app(app)


    return app

def register_blueprint(app):

    from main.urls import main as main_blueprint
    from accounts.urls import accounts as accounts_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(accounts_blueprint, url_prefix='/accounts')

    return app

class GitmarkApp(object):
    def __init__(self, config_name='default'):
        self.app = Flask(__name__, 
        template_folder=config[config_name].TEMPLATE_PATH, static_folder=config[config_name].STATIC_PATH)

        app = self.app
        
        app.config.from_object(config[config_name])

        config[config_name].init_app(app)

        db.init_app(app)
        login_manager.init_app(app)
        principals.init_app(app)


    def register_blueprint(self):
        app = self.app
        from main.urls import main as main_blueprint
        from accounts.urls import accounts as accounts_blueprint

        app.register_blueprint(main_blueprint)
        app.register_blueprint(accounts_blueprint, url_prefix='/accounts')

        return app


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

app = create_app()
celery_app = make_celery(app)