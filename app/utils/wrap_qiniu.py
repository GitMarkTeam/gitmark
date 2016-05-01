#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gitmark.config import GitmarkSettings

import qiniu

QINIU_ACCESS_KEY = GitmarkSettings['qiniu']['access_key']
QINIU_SECRET_KEY = GitmarkSettings['qiniu']['secret_key']
QINIU_BUCKET_NAME = GitmarkSettings['qiniu']['bucket_name']
QINIU_URL = GitmarkSettings['qiniu']['base_url']

def qiniu_fetch_img(img_url, img_name):
    q = qiniu.Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    token = q.upload_token(QINIU_BUCKET_NAME)

    bucket = qiniu.BucketManager(q)
    ret, info = bucket.fetch(img_url, QINIU_BUCKET_NAME, img_name)

    if not ret:
        return None

    key = ret.get('key')
    return QINIU_URL + key
    # print dir(qiniu)
    # return 'aa'



