from datetime import datetime
from flask import url_for

import markdown2

from gitmark import db


class GitmarkMeta(db.Document):
    key = db.StringField(max_length=64)
    value = db.StringField()
    value_list = db.ListField(db.StringField())
    value_dict = db.DictField()

class Repo(db.Document):
    name = db.StringField(max_length=128)
    full_name = db.StringField(max_length=128, unique=True)
    link = db.URLField()
    author = db.StringField(max_length=128)
    author_link = db.URLField(required=False)
    desc = db.StringField()
    language = db.StringField(max_length=64)
    create_time = db.DateTimeField()
    update_time = db.DateTimeField()
    starred_users = db.ListField(db.StringField()) 
    tags = db.ListField(db.StringField(max_length=30))

    def save(self, *args, **kwargs):
        if not self.create_time:
            self.create_time = datetime.now()
        self.update_time = datetime.now()
        return super(Repo, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.full_name

    meta = {
        'allow_inheritance': True,
        'indexes': ['full_name'],
        'ordering': ['-create_time']
    }


class Collection(db.Document):
    name = db.StringField(max_length=128)
    description = db.StringField()
    owner = db.StringField(max_length=128)
    is_private = db.BooleanField(default=False)
    repos = db.ListField(db.DictField())
    last_update = db.DateTimeField()
    create_date = db.DateTimeField()

    meta = {
        'allow_inheritance': True,
        'indexes': ['name'],
        'ordering': ['-create_date']
    }

    def save(self, *args, **kwargs):
        if not self.create_date:
            self.create_date = datetime.now()
        self.last_update = datetime.now()
        return super(Collection, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{0} -> {1}'.format(self.owner, self.name)