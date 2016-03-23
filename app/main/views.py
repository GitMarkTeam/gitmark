from flask import request, redirect, render_template, url_for, abort, flash
from flask import current_app, make_response
from flask.views import MethodView

from flask.ext.login import login_required, current_user
from . import tasks

def hello():
    return 'hello, world'

def index():
    # return 'index'
    return render_template('main/index.html')

def test_celery():
    tasks.test_celery.delay()
    return 'checkout shell to get test result'
