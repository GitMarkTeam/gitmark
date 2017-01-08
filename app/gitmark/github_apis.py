#!/usr/bin/env python
# -*- coding: utf-8 -*-

base_url = 'https://api.github.com'

def auth_user():
    api = '/user'
    url = base_url + api
    return url

def user_repos(username):
    api = '/users/{0}/starred'.format(username)
    url = base_url + api
    return url

def search_repos(q, sort=None, order='desc'):
    api = u'/search/repositories?q={0}'.format(q)
    if sort:
        api = '{0}&sort={1}&order={2}'.format(api, sort, order)

    return base_url+api