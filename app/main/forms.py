#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, URL, Optional
# from flask.ext.login import current_user
# from flask.ext.mongoengine.wtf import model_form

from . import models

class CollectionForm(Form):
    name = StringField()
    description = TextAreaField()