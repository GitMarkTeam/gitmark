from flask import Blueprint

from . import views

main = Blueprint('main', __name__)

main.add_url_rule('/hello/', 'hello', views.hello)
main.add_url_rule('/', 'index', views.index)