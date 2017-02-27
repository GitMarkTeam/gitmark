#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, logging

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    handlers = {
        'console': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG},
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'JuneMessage.log',
            'formatter': 'f'},
        },
    root = {
        'handlers': ['console', 'file'],
        'level': logging.DEBUG,
        },
)


GitmarkSettings = {
    'allow_registration': os.environ.get('allow_registration', 'true').lower() == 'true',
    'allow_su_creation': os.environ.get('allow_su_creation', 'false').lower() == 'true',
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
    },
    'default_user_image': os.environ.get('DEFAULT_USER_IMAGE') or 'http://gitmark-staff.igevin.info/github_avatar_username.jpeg',
    
        
}


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

    #########################
    # email server
    #########################
    # MAIL_SERVER = 'smtp.gmail.com'
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.mxhichina.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


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

    # BROKER_URL = 'redis://localhost:6379/0'
    # CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

    # BROKER_URL = 'redis://:{password}@{hostname}:{port}/0'.format(password=os.environ['REDIS_PASSWORD'], hostname=os.environ['REDIS_PORT_6379_TCP_ADDR'], port=os.environ['REDIS_PORT_6379_TCP_PORT'])
    # CELERY_RESULT_BACKEND = 'redis://:{password}@{hostname}:{port}/1'.format(password=os.environ['REDIS_PASSWORD'], hostname=os.environ['REDIS_PORT_6379_TCP_ADDR'], port=os.environ['REDIS_PORT_6379_TCP_PORT'])

    BROKER_URL = os.environ.get('BROKER_URL') or 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://redis:6379/1'


config = {
    'dev': DevConfig,
    'prd': PrdConfig,
    'default': DevConfig,
}
