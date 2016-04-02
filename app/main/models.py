from datetime import datetime
from flask import url_for

import markdown2

from gitmark import db
# from accounts.Documents import User

# class Post(db.Document):
#     title = db.StringField(max_length=255, default='new blog', required=True)
#     slug = db.StringField(max_length=255, required=True, unique=True)
#     fix_slug = db.StringField(max_length=255, required=False)
#     abstract = db.StringField()
#     raw = db.StringField(required=True)
#     pub_time = db.DateTimeField(required=True)
#     update_time = db.DateTimeField(required=True)
#     content_html = db.StringField(required=True)
#     author = db.ReferenceField(User)
#     category = db.StringField(max_length=64, default='default')
#     tags = db.ListField(db.StringField(max_length=30))
#     is_draft = db.BooleanField(default=False)
#     post_type = db.StringField(max_length=64, default='post')

#     def get_absolute_url(self):
#         return url_for('main.post_detail', slug=self.slug)

#     def save(self, allow_set_time=False, *args, **kwargs):
#         if not allow_set_time:
#             now = datetime.datetime.now()
#             if not self.pub_time:
#                 self.pub_time = now
#             self.update_time = now
#         # self.content_html = self.raw
#         self.content_html = markdown2.markdown(self.raw, extras=['code-friendly', 'fenced-code-blocks']).encode('utf-8')
#         return super(Post, self).save(*args, **kwargs)

#     def set_post_date(self, pub_time, update_time):
#         self.pub_time = pub_time
#         self.update_time = update_time
#         return self.save(allow_set_time=True)

#     def __unicode__(self):
#         return self.title

#     meta = {
#         'allow_inheritance': True,
#         'indexes': ['slug'],
#         'ordering': ['-pub_time']
#     }


# class GitMarkMeta(db.Document):
#     key = db.StringField(max_length=256)
#     value = db.StringField(max_length=256, null=True, blank=True)
#     flag = db.BooleanField(default=False)
#     misc = db.StringField(max_length=256, null=True, blank=True)

#     def __unicode__(self):
#         return self.key


class GitmarkMeta(db.Document):
    key = db.StringField(max_length=64)
    value_list = db.ListField(db.StringField())

class Repo(db.Document):
    name = db.StringField(max_length=128)
    full_name = db.StringField(max_length=128, unique=True)
    link = db.URLField()
    author = db.StringField(max_length=128)
    author_link = db.URLField(required=False)
    desc = db.StringField()
    language = db.StringField(max_length=64)
    create_time = db.DateTimeField(required=True, default=datetime.now())
    update_time = db.DateTimeField(required=True, default=datetime.now())
    starred_users = db.ListField(db.StringField()) 
    tags = db.ListField(db.StringField(max_length=30))

    def save(self, *args, **kwargs):
        self.update_time = datetime.now()
        return super(Repo, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.full_name

    meta = {
        'allow_inheritance': True,
        'indexes': ['full_name'],
        'ordering': ['-create_time']
    }


# class Collection(db.Document):
#     name = db.StringField(max_length=128)
#     description = db.StringField(blank=True)
#     user = db.ForeignKey(User)
#     repos = db.ManyToManyField(Repo, blank=True)
#     last_update = db.DateTimeField(auto_now=True)
#     create_date = db.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-create_date']

#     def __unicode__(self):
#         return self.user.username + '->' + self.name