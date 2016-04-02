#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import models


def import_repos(github_starred_repos, gitmark_user=None):
    for starred_repo in github_starred_repos:
        language = starred_repo.get('language') or 'unknown'

        obj = models.GitmarkMeta.objects(key='language').first()
        if not obj:
            models.GitmarkMeta.objects(key='language').update_one(set__key='language', upsert=True)

        models.GitmarkMeta.objects(key='language').update_one(add_to_set__value_list=language, upsert=True)

        models.Repo.objects(full_name=starred_repo.get('full_name')).update_one(upsert=True, 
                set_name=starred_repo.get('name'),
                set_link=starred_repo.get('html_url'),
                set_author=starred_repo.get('owner').get('login'),
                set_author_link=starred_repo.get('owner').get('html_url'),
                set_desc=starred_repo.get('description'),
                set_language=language,
                add_to_set__starred_users=gitmark_user
            )
