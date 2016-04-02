#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys

# from env import github, qiniu

GitmarkSettings = {
    # 'post_types': ('post', 'page'),
    'allow_registration': os.environ.get('allow_registration', 'true').lower() == 'true',
    'allow_su_creation': os.environ.get('allow_su_creation', 'true').lower() == 'true',
    # 'allow_donate': os.environ.get('allow_donate', 'true').lower() == 'true',
    # 'auto_role': os.environ.get('auto_role', 'reader').lower(),
    # 'gitmark_meta': {
    #     'name': os.environ.get('name').decode('utf8') if os.environ.get('name') else 'Oct Blog',
    #     'subtitle': os.environ.get('subtitle').decode('utf8') if os.environ.get('subtitle') else 'Oct Blog Subtitle',
    #     'description': os.environ.get('description').decode('utf8') if os.environ.get('description') else 'Oct Blog Description',
    #     'owner': os.environ.get('owner').decode('utf8') if os.environ.get('owner') else 'Gevin',
    #     'keywords': os.environ.get('keywords').decode('utf8') if os.environ.get('keywords') else 'python,django,flask,docker,MongoDB',
    #     'google_site_verification': os.environ.get('google_site_verification') or '12345678',
    #     'baidu_site_verification': os.environ.get('baidu_site_verification') or '87654321',
    # },
    'pagination':{
        'per_page': int(os.environ.get('per_page', 10)),
        'admin_per_page': int(os.environ.get('admin_per_page', 20)),
        'archive_per_page': int(os.environ.get('admin_per_page', 50)),
    },
    'github': {
        'client_id': os.environ.get('GITHUB_ID'),
        'client_secret': os.environ.get('GITHUB_SECRET'),
        'app_user': os.environ.get('APP_USER'),
        'app_pass': os.environ.get('APP_PASS'),
        'page_limit_large': 100,
        'page_limit_medium': 50,
        'page_limit_small': 30,
    },
    'qiniu':{
        'access_key': os.environ.get('QINIU_AK'),
        'secret_key': os.environ.get('QINIU_SK'),
        'bucket_name': os.environ.get('BUCKET'),
        'base_url': os.environ.get('QINIU_URL'),
    }
    # 'blog_comment':{
    #     'allow_comment': os.environ.get('allow_comment', 'true').lower() == 'true',
    #     'comment_type': os.environ.get('comment_type', 'duoshuo').lower(), # currently, OctBlog only supports duoshuo comment
    #     'comment_opt':{
    #         'duoshuo': 'oct-blog', # shotname of duoshuo
    #         }
    # },
    # 'allow_share_article': os.environ.get('allow_share_article', 'true').lower() == 'true',
        
}

# CeleryConfig = {
#     'CELERY_BROKER_URL': 'redis://localhost:6379/0',
#     'CELERY_RESULT_BACKEND': 'redis://localhost:6379/1',
#     'CELERY_TASK_SERIALIZER': 'json',
#     'CELERY_RESULT_SERIALIZER': 'json',
#     'CELERY_ACCEPT_CONTENT':['json'],
#     'CELERY_TIMEZONE': 'Asia/Shanghai',
#     'CELERY_ENABLE_UTC': True,
#     'CELERY_IGNORE_RESULT': False,
# }

class CeleryConfig(object):
    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT=['json']
    CELERY_TIMEZONE = 'Asia/Shanghai'
    CELERY_ENABLE_UTC = True
    CELERY_IGNORE_RESULT = False
    CELERY_IMPORTS = ('main.tasks')

class Config(object):
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fjdlj*^fge$LJDL08_80jflKzcznv*c'
    MONGODB_SETTINGS = {'DB': 'Gitmark'}

    TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates').replace('\\', '/')
    STATIC_PATH = os.path.join(BASE_DIR, 'static').replace('\\', '/')


    ########################
    # Celery Config
    ########################

    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT=['json']
    CELERY_TIMEZONE = 'Asia/Shanghai'
    CELERY_ENABLE_UTC = True
    CELERY_IGNORE_RESULT = False
    CELERY_IMPORTS = ('main.tasks')


    @staticmethod
    def init_app(app):
        pass

class DevConfig(Config):
    DEBUG = True

class PrdConfig(Config):
    # DEBUG = False
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    MONGODB_SETTINGS = {
            'db': 'Gitmark',
            'host': os.environ.get('MONGO_HOST') or 'localhost',
            # 'port': 12345
        }


config = {
    'dev': DevConfig,
    'prd': PrdConfig,
    'default': DevConfig,
}
