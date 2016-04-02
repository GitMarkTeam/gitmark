#!/usr/bin/env python
# -*- coding: utf-8 -*-

base_url = 'https://api.github.com'

def auth_user():
    api = '/user'
    url = base_url + api
    return url

def starred_repos(username, page=1, per_page=100):
    api = '/users/{0}/starred'.format(username)
    url = base_url + api
    return '{url}?page={page}&per_page={per_page}'.format(url=url, page=page, per_page=per_page)

# def starred_repos(username, page, per_page=100):
#     return 'https://api.github.com/users/{0}/starred?page={1}&per_page={2}'.format(username, page, per_page)