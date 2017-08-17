#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json, os
try:
    from itertools import filterfalse
except ImportError:
    # python 2
    from itertools import ifilterfalse as filterfalse

import requests

from flask import request, redirect, render_template, url_for, abort, flash, session, jsonify
from flask import current_app, make_response, send_from_directory
from flask.views import MethodView

from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

from . import models, tasks, forms
from gitmark.config import GitmarkSettings
from gitmark import github_apis
from accounts import github_auth
from accounts.permissions import admin_permission
from accounts import models as accounts_models

PER_PAGE = GitmarkSettings['pagination']['per_page']
app_user = GitmarkSettings['github']['app_user']
app_pass = GitmarkSettings['github']['app_pass']

class EnterpriseView(MethodView):
    template_name = 'main/enterprise.html'
    def get(self):
        return render_template(self.template_name)

class IndexView(MethodView):
    # decorators = [login_required, ]
    template_name = 'main/index.html'

    def display_enterprise_page(self):
        enterprise_view = EnterpriseView()
        return enterprise_view.get()

    def get(self):
        if current_user.is_anonymous:
            return self.display_enterprise_page()

        data = {}
        data['user'] = current_user
        starred_repos = models.Repo.objects(starred_users=current_user.username)
        collections = models.Collection.objects(owner=current_user.username)
        following_collections = models.Collection.objects(followers=current_user.username)


        data['starred_repos'] = starred_repos
        data['collections'] = collections
        data['following_collections'] = following_collections


        data['is_public'] = False

        return render_template(self.template_name, **data)

    def post(self):
        if current_user.is_anonymous:
            return self.display_enterprise_page()

        if request.form.get('link_github'):
            session['oauth_callback_type'] = 'link_github'
            return github_auth.github_auth()

        elif request.form.get('rm_github'):
            current_user.github_username = ''
            current_user.github = None
            current_user.save()


        return redirect(url_for('main.index'))


class UserView(MethodView):
    # decorators = [login_required, ]
    template_name = 'main/index.html'

    def get(self, username):
        data = {}
        # current_user_name = username or current_user.username
        user = accounts_models.User.objects.get_or_404(username=username)

        data['user'] = user
        starred_repos = models.Repo.objects(starred_users=username)
        collections = models.Collection.objects(owner=username, is_private=False)
        following_collections = models.Collection.objects(followers=username)


        data['starred_repos'] = starred_repos
        data['collections'] = collections
        data['following_collections'] = following_collections


        data['is_public'] = True
        data['username'] = username

        return render_template(self.template_name, **data)

class StarredRepoView(MethodView):
    decorators = [login_required, ]
    template_name = 'main/starred_repo.html'

    def get(self, username=None):
        if not username:
            username = current_user.username
        repos = models.Repo.objects(starred_users=username)
        # languages = models.GitmarkMeta.objects(key='language').first()
        try:
            languages = models.GitmarkMeta.objects.get(key='language')
        except models.GitmarkMeta.DoesNotExist:
            languages = models.GitmarkMeta(key='languages')
            languages.save()

        cur_page = request.args.get('page', 1)
        cur_language = request.args.get('language')

        repos = repos.filter(language=cur_language) if cur_language else repos
        url_params = 'language={0}'.format(cur_language) if cur_language else None

        repos = repos.paginate(page=int(cur_page), per_page=PER_PAGE)

        #group by aggregate
        language_cursor = models.Repo._get_collection().aggregate([
                {
                    '$match': {'starred_users': current_user.username}
                },
                { '$group' :
                    { '_id' : {'language' : '$language' },
                      'name' : { '$first' : '$language' },
                      'count' : { '$sum' : 1 },
                    }
                }
            ])

        data = { 'starred_repos':repos, 'languages':languages.value_list, 'cur_language':cur_language,
            'url_params':url_params }

        data['language_cursor'] = language_cursor

        return render_template(self.template_name, **data)

class ImportRepoView(MethodView):
    decorators = [login_required,]
    template_name = 'main/import_repo.html'

    def get(self, starred=False):
        data = {'starred':starred}
        return render_template(self.template_name, **data)

    def post(self, starred=True):
        if request.form.get('import_mine'):
            github_user = current_user.github_username
            if not github_user:
                msg = 'You have not associated with GitHub yet'
                flash(msg)
                # url = reverse('main:admin_index')
                return redirect(url_for('main.index'))

        else:
            github_user = request.form.get('github_username')

        tasks.import_github_repos.delay(github_user, gitmark_username=current_user.username if starred else None)

        msg = 'Start importing at background'
        flash(msg)
        return redirect('.')



class ReposView(MethodView):
    # decorators = [login_required, admin_permission.require(401),]
    decorators = [login_required]
    template_name = 'main/repos.html'

    def get(self):
        repos = models.Repo.objects().all()
        languages = models.GitmarkMeta.objects(key='language').first()

        cur_page = request.args.get('page', 1)
        cur_language = request.args.get('language')

        repos = repos.filter(language=cur_language) if cur_language else repos
        url_params = 'language={0}'.format(cur_language) if cur_language else None

        repos = repos.paginate(page=int(cur_page), per_page=PER_PAGE)

        #group by aggregate
        # language_cursor = models.Repo._get_collection().aggregate([
        #         {
        #             '$match': {'starred_users': current_user.username}
        #         },
        #         { '$group' :
        #             { '_id' : {'language' : '$language' },
        #               'name' : { '$first' : '$language' },
        #               'count' : { '$sum' : 1 },
        #             }
        #         }
        #     ])

        data = { 'repos':repos, 'languages':languages.value_list if languages else [], 'cur_language':cur_language,
            'url_params':url_params }

        # data['language_cursor'] = language_cursor

        return render_template(self.template_name, **data)

class GitHubResultView(MethodView):
    decorators = [login_required]
    template_name = 'main/github_result.html'

    def get(self):
        key = request.args.get('key')
        if not key or not key.strip():
            return redirect('main:index')


        api = github_apis.search_repos(q=key.strip())
        res = requests.get(api, auth=(app_user, app_pass))
        result = res.json()
        data = {'result':result}


        has_items = result['total_count'] > 0
        data['has_items'] = has_items

        if has_items:
            collections = models.Collection.objects(owner=current_user.username)
            data['collections'] = collections
            repos = []

            for item in result['items']:
                repo = {
                    'name': item['name'],
                    'full_name': item['full_name'],
                    'link': item['html_url'],
                    'author': item['owner']['login'],
                    'author_link': item['owner']['html_url'],
                    'desc': item['description'],
                    'language': item['language']
                }

                repos.append(repo)

            data['repos'] = repos
            # return jsonify({'repos':repos})



        return render_template(self.template_name, **data)

    def post(self):
        repos = request.form.getlist('repos')
        repos = [ self.get_repo(json.loads(repo)) for repo in repos]

        collection_ids = request.form.getlist('collections')

        if request.form.get('add_to_collection'):
            for collection_id in collection_ids:
                try:
                    collection = models.Collection.objects.get(id=collection_id)
                    self.add_repos_to_collections(repos, collection)

                except models.Collection.DoesNotExist:
                    pass

            msg = 'Repos have been added to collections'
            flash(msg, 'success')
            return redirect(url_for('main.my_collections'))


        self.star_repos(repos)
        msg = 'Repos have been starred'
        flash(msg, 'success')
        return redirect(url_for('main.starred_repos'))



    def get_repo(self, repo_dict):
        try:
            repo = models.Repo.objects.get(full_name=repo_dict['full_name'])

            detail_changed = False

            if repo.name != repo_dict['name']:
                repo.name = repo_dict['name']
                detail_changed = True
            if repo.link != repo_dict['link']:
                repo.link = repo_dict['link']
                detail_changed = True
            if repo.author != repo_dict['author']:
                repo.author = repo_dict['author']
                detail_changed = True
            if repo.author_link != repo_dict['author_link']:
                repo.author_link = repo_dict['author_link']
                detail_changed = True
            if repo.desc != repo_dict['desc']:
                repo.desc = repo_dict['desc']
                detail_changed = True
            if repo.language != repo_dict.get('language'):
                repo.desc = repo_dict.get('language') or 'unknown'
                detail_changed = True

            if detail_changed:
                repo.save()

        except models.Repo.DoesNotExist:
            repo = models.Repo()
            repo.name = repo_dict['name']
            repo.full_name = repo_dict['full_name']
            repo.link = repo_dict['link']
            repo.author = repo_dict['author']
            repo.author_link = repo_dict['author_link']
            repo.desc = repo_dict['desc']
            repo.language = repo_dict.get('language') or 'unknown'
            repo.save()

        return repo

    # def add_repos_to_collections(self, repos, collection):

    #     repos_list = [ {'id':repo.id, 'link':repo.link, 'full_name':repo.full_name, 'desc':repo.desc, 'language':repo.language } for repo in repos]

    #     collection.modify(push_all__repos=repos_list)
    #     collection.modify(set__last_update=datetime.now())

    def add_repos_to_collections(self, repos, collection):

        repos_list = [ {'id':repo.id, 'link':repo.link, 'full_name':repo.full_name, 'desc':repo.desc, 'language':repo.language } for repo in repos]
        exist_repos = collection.repos

        diff_repos = list(filterfalse(lambda repo: repo in exist_repos, repos_list))

        collection.modify(push_all__repos=diff_repos)
        collection.modify(set__last_update=datetime.now())


    def star_repos(self, repos):
        for repo in repos:
            repo.modify(add_to_set__starred_users=current_user.username)
