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