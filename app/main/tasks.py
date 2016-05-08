#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from gitmark import create_app, make_celery, celery_app
from gitmark.config import GitmarkSettings

from utils import github_api

# from misc import import_repos
from . import models

app_user = GitmarkSettings['github']['app_user']
app_pass = GitmarkSettings['github']['app_pass']
# github_per_page = settings.GITMARK['GITHUB']['page_limit_large']
# app = create_app()
# celery_app = make_celery(app)


@celery_app.task(name='gitmark.test_celery')
def test_celery():
    print 'hello, world'

# @celery_app.task(name='gitmark.import_starred_repos')
# def import_github_starred_repos(github_username, gitmark_username):
#     # cur_user = User.objects.get(username=gitmark_username)
#     page = 1
#     api = github_api.starred_repos(github_username, page)
#     res = requests.get(api, auth=(app_user, app_pass))

#     starred_repos = res.json()

#     # GitHub API rate limit exceeded 
#     if not isinstance(starred_repos, list):
#         print 'GitHub API rate limit exceeded '
#         return

#     while len(starred_repos) > 0:
#         import_repos(starred_repos, gitmark_user=gitmark_username)

#         page += 1
#         api = github_api.starred_repos(github_username, page)
#         res = requests.get(api, auth=(app_user, app_pass))

#         if res.status_code != 200:
#             # print 'GitHub API rate limit exceeded '
#             return

#         starred_repos = res.json()
#         # print page
#     # print cur_user.id

def import_repos(github_starred_repos, gitmark_user=None):
    for starred_repo in github_starred_repos:
        language = starred_repo.get('language') or 'unknown'

        obj = models.GitmarkMeta.objects(key='language').first()
        if not obj:
            models.GitmarkMeta.objects(key='language').update_one(set__key='language', upsert=True)

        models.GitmarkMeta.objects(key='language').update_one(add_to_set__value_list=language, upsert=True)

        models.Repo.objects(full_name=starred_repo.get('full_name')).update_one(upsert=True, 
                set__name=starred_repo.get('name'),
                set__link=starred_repo.get('html_url'),
                set__author=starred_repo.get('owner').get('login'),
                set__author_link=starred_repo.get('owner').get('html_url'),
                set__desc=starred_repo.get('description'),
                set__language=language,
                add_to_set__starred_users=gitmark_user
            )

@celery_app.task(name='gitmark.import_repos')
def import_github_repos(github_username, gitmark_username=None):
    page = 1
    api = github_api.starred_repos(github_username, page)
    res = requests.get(api, auth=(app_user, app_pass))
    # print api, app_user, app_pass

    starred_repos = res.json()
    # print starred_repos

    # GitHub API rate limit exceeded 
    if not isinstance(starred_repos, list):
        print 'GitHub API rate limit exceeded '
        print res.status_code
        print res.text
        return

    while len(starred_repos) > 0:
        import_repos(starred_repos, gitmark_user=gitmark_username)

        page += 1
        api = github_api.starred_repos(github_username, page)
        res = requests.get(api, auth=(app_user, app_pass))

        if res.status_code != 200:
            # print 'GitHub API rate limit exceeded '
            return

        starred_repos = res.json()

def import_github_repos2(github_username, gitmark_username=None):
    page = 1
    api = github_api.starred_repos(github_username, page)
    res = requests.get(api, auth=(app_user, app_pass))
    # print api, app_user, app_pass

    starred_repos = res.json()
    # print starred_repos

    # GitHub API rate limit exceeded 
    if not isinstance(starred_repos, list):
        print 'GitHub API rate limit exceeded '
        return

    while len(starred_repos) > 0:
        import_repos(starred_repos, gitmark_user=gitmark_username)

        page += 1
        api = github_api.starred_repos(github_username, page)
        res = requests.get(api, auth=(app_user, app_pass))

        if res.status_code != 200:
            # print 'GitHub API rate limit exceeded '
            return

        starred_repos = res.json()

