from flask import Blueprint

from . import views

main = Blueprint('main', __name__)

main.add_url_rule('/hello/', 'hello', views.hello)
main.add_url_rule('/', 'index', views.index)
main.add_url_rule('/test-celery/', 'test-celery', views.test_celery)