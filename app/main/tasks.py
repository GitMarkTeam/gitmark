#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from gitmark import celery_app

# app_user = settings.GITMARK['GITHUB']['app_user']
# app_pass = settings.GITMARK['GITHUB']['app_pass']
# github_per_page = settings.GITMARK['GITHUB']['page_limit_large']


@celery_app.task(name='gitmark.test_celery')
def test_celery():
    print 'hello, world'

# @celery_app.task(name='gitmark.import_starred_repos')
# def import_github_starred_repos(github_username, gitmark_username):
#     cur_user = User.objects.get(username=gitmark_username)
#     page = 1
#     api = functions.build_github_starred_api(github_username, page)
#     res = requests.get(api, auth=(app_user, app_pass))

#     # print app_user, app_pass, res.status_code
#     # res = requests.get(api)
#     starred_repos = res.json()
#     # print page

#     # GitHub API rate limit exceeded 
#     if not isinstance(starred_repos, list):
#         print 'GitHub API rate limit exceeded '
#         return

#     while len(starred_repos) > 0:
#         functions.import_repos(starred_repos, gitmark_user=cur_user)

#         page += 1
#         api = functions.build_github_starred_api(github_username, page)
#         res = requests.get(api, auth=(app_user, app_pass))
#         # res = requests.get(api)
#         if res.status_code != 200:
#             # print 'GitHub API rate limit exceeded '
#             return
#         starred_repos = res.json()
#         # print page
#     # print cur_user.id

# @celery_app.task(name='gitmark.import_repos')
# def import_github_repos(github_username, gitmark_username=None):
#     cur_user = User.objects.get(username=gitmark_username) if gitmark_username else None

#     api = github_apis.user_repos(github_username) 

#     params = {'page': 1, 'per_page':github_per_page}
#     res = requests.get(api, auth=(app_user, app_pass), params=params)

#     # GitHub API rate limit exceeded 
#     if res.status_code != 200:
#         # print 'GitHub API rate limit exceeded'
#         return


#     starred_repos = res.json()
#     # print 'Page: {0}, repo count: {1}'.format(params['page'], len(starred_repos))

#     while len(starred_repos) > 0:
#         functions.import_repos(starred_repos, gitmark_user=cur_user)

#         params['page'] += 1
#         res = requests.get(api, auth=(app_user, app_pass), params=params)

#         if res.status_code != 200:
#             # print 'GitHub API rate limit exceeded '
#             return

#         starred_repos = res.json()
#         # print 'Page: {0}, repo count: {1}'.format(params['page'], len(starred_repos))


