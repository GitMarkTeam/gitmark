#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, URL, Optional

from . import models

class CollectionForm(FlaskForm):
    name = StringField()
    is_private = BooleanField(default=False)
    tags_str = StringField('Tags')
    description = TextAreaField()