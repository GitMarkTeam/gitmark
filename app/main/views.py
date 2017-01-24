#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json

import requests

from flask import request, redirect, render_template, url_for, abort, flash, session, jsonify
from flask import current_app, make_response
from flask.views import MethodView

from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q

from . import models, tasks, forms
from gitmark.config import GitmarkSettings
from gitmark import github_apis
from accounts import github_auth
from accounts.permissions import admin_permission

PER_PAGE = GitmarkSettings['pagination']['per_page']
app_user = GitmarkSettings['github']['app_user']
app_pass = GitmarkSettings['github']['app_pass']

def hello():
    return 'hello, world'


def test_celery():
    tasks.test_celery.delay()
    return 'checkout shell to get test result'

def test():
    # try:
    #     obj = models.GitmarkMeta.objects.get(key='language')
    # except models.GitmarkMeta.DoesNotExist:
    #     return 'DoesNotExist'

    # return 'got'

    # pre = models.GitmarkMeta(key='test')
    # pre.save()

    # models.GitmarkMeta.objects(key='test').update_one(add_to_set__value_list='test')
    # models.GitmarkMeta.objects(key='test').delete()
    # obj = models.GitmarkMeta.objects(key='test4').first()
    # return str(obj == None)
    # models.GitmarkMeta.objects(key='test2').update_one(add_to_set__value_list=None, upsert=True)
    # models.GitmarkMeta.objects(key='test3').update_one(set__key='test3', upsert=True)
    # obj = models.GitmarkMeta.objects(key='test2').first()
    obj = models.GitmarkMeta.objects(key='language').first()
    if obj == None:
        return 'None'
    return str(obj.value_list)
    return 'true'

class IndexView(MethodView):
    decorators = [login_required, ]
    template_name = 'main/index.html'

    def get(self):
        data = {}
        starred_repos = models.Repo.objects(starred_users=current_user.username)
        collections = models.Collection.objects(owner=current_user.username)

        data['starred_repos'] = starred_repos
        data['collections'] = collections


        # starred_repos_count = starred_repos.count()
        # collections_count = 

        return render_template(self.template_name, **data)

    def post(self):
        if request.form.get('link_github'):
            session['oauth_callback_type'] = 'link_github'           
            return github_auth.github_auth()
        
        elif request.form.get('rm_github'):
            current_user.github_username = ''
            # current_user.github = ''
            current_user.save()

        
        return redirect(url_for('main.index')) 

# class UserView(MethodView):
#     template_name = 'main/index.html'

#     def get(self, username):
#         data = {}
#         starred_repos = models.Repo.objects(starred_users=username)
#         collections = models.Collection.objects(owner=username, is_private=False)

#         data['starred_repos'] = starred_repos
#         data['collections'] = collections


#         # starred_repos_count = starred_repos.count()
#         # collections_count = 

#         return render_template(self.template_name, **data)

class StarredRepoView(MethodView):
    decorators = [login_required, ]
    template_name = 'main/starred_repo.html'

    def get(self):
        repos = models.Repo.objects(starred_users=current_user.username)
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

class MyCollectionsView(MethodView):
    decorators = [login_required]
    template_name = 'main/collections.html'

    def get(self, form=None):
        if not form:
            form = forms.CollectionForm()
        collections = models.Collection.objects(owner=current_user.username)

        data = { 'collections':collections, 'form':form }

        return render_template(self.template_name, **data)

    def post(self):
        form = forms.CollectionForm(obj=request.form)
        if form.validate():
            collection = models.Collection()
            collection.name = form.name.data
            collection.description = form.description.data
            collection.owner = current_user.username
            collection.is_private = form.is_private.data

            collection.save()

            return redirect(url_for('main.my_collections'))

        return self.get(form=form)

class UserCollectionsView(MethodView):
    template_name = 'main/collections_user_public.html'

    def get(self, username):
        collections = models.Collection.objects(owner=username, is_private=False)

        data = { 'collections':collections}

        return render_template(self.template_name, **data)

class MyCollectionEditView(MethodView):
    decorators = [login_required, ]
    template_name = 'main/simple_form.html'

    def get(self, collection_id, form=None):
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()
        if not collection:
            return 'no collection', 404

        if not form:
            form = forms.CollectionForm(obj=collection)

        data = {'form':form}
        return render_template(self.template_name, **data)

    def post(self, collection_id, form=None):
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()
        if not collection:
            return 'no collection', 404

        form = forms.CollectionForm(obj=request.form)
        name = form.name.data
        description = form.description.data
        is_private = form.is_private.data

        collection.name = name
        collection.description = description
        collection.is_private = is_private

        collection.save()
        msg = 'Succeed to update this collection'
        flash(msg, 'success')

        return redirect(url_for('main.my_collections'))

    def delete(self, collection_id):
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()

        if collection:
            collection.delete()

        if request.args.get('ajax'):
            return 'success'

        msg = 'Succeed to delete the collection'
        flash(msg, 'success')

        return redirect(url_for('main.my_collections'))

class CollectionView(MethodView):
    template_name = 'main/collection.html'
    def get(self, collection_id):
        collection = models.Collection.objects(id=collection_id).first()
        if not collection:
            return 'no collection', 404

        data = {'cur_collection': collection, 'collections':None}

        if not current_user.is_anonymous:
            collections = models.Collection.objects(owner=collection.owner)
        else:
            collections = models.Collection.objects(owner=collection.owner, is_private=False)
        
        data['collections'] = collections

        return render_template(self.template_name, **data)

    def delete(self, collection_id):
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()

        if not collection:
            return 'No collection found', 404

        collection.modify(pull_all__repos=collection.repos)
        collection.modify(set__last_update=datetime.now())

        if request.args.get('ajax'):
            return 'success'

        msg = 'Succeed to clear the collection'
        flash(msg, 'success')

        return redirect(url_for('main.my_collections'))

class CollectionDetailEditView(MethodView):
    template_name = 'main/collection_detail_edit.html'
    decorators = [login_required]

    def get(self, collection_id):
        collection = models.Collection.objects(id=collection_id, owner=current_user.username).first()
        if not collection:
            return 'no collection', 404

        repo_ids = [repo['id'] for repo in collection.repos]
        languages = models.GitmarkMeta.objects(key='language').first()

        starred = True

        diff_starred_repos = models.Repo.objects(starred_users=current_user.username, id__nin=repo_ids)

        cur_page = request.args.get('page', 1)
        cur_language = request.args.get('language')

        diff_starred_repos = diff_starred_repos.filter(language=cur_language) if cur_language else diff_starred_repos
        diff_starred_repos = diff_starred_repos.paginate(page=int(cur_page), per_page=PER_PAGE)

        url_params = 'language={0}'.format(cur_language) if cur_language else None

        data = { 'diff_starred_repos':diff_starred_repos, 'languages':languages.value_list, 'cur_language':cur_language, 'collection':collection, 'url_params':url_params, 'starred':starred }

        return render_template(self.template_name, **data)

    def post(self, collection_id):
        collection = models.Collection.objects(id=collection_id, owner=current_user.username).first()
        if not collection:
            return 'no collection', 404

        repo_ids = request.form.getlist('repos')
        repos2collect = models.Repo.objects(id__in=repo_ids)

        repos = [ {'id':repo.id, 'link':repo.link, 'full_name':repo.full_name, 'desc':repo.desc, 'language':repo.language } for repo in repos2collect]

        collection.modify(push_all__repos=repos)
        collection.modify(set__last_update=datetime.now())

        msg = 'Succeed to add to the collection'
        flash(msg, 'success')

        return redirect(url_for('main.collection_detail', collection_id=collection_id))

    def delete(self, collection_id):
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()
        if not collection:
            return 'No collection found', 404

        full_name = request.args.get('full_name')
        repos = collection.repos
        filtered_repos = filter(lambda x:x['full_name']==full_name, repos)
        
        try:
            collection.modify(pull__repos=filtered_repos[0])
        except:
            pass

        if request.args.get('ajax'):
            return 'success'

        msg = 'Succeed to clear the collection'
        flash(msg, 'success')

        return redirect(url_for('main.my_collections'))

class Search4Collection(MethodView):
    decorators = [login_required]
    template_name = 'main/collection_search.html'

    def get(self, collection_id):
        data = {}
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()
        if not collection:
            return 'No collection found', 404
        data['collection'] = collection

        repo_ids = [repo['id'] for repo in collection.repos]
        repos = models.Repo.objects(id__nin=repo_ids)

        keyword = request.args.get('keyword')
        flag = request.args.get('flag')
        data['keyword'] = keyword
        data['flag'] = flag
        if flag:
            url_params = 'keyword={0}&flag={1}'.format(keyword, flag)
            data['url_params'] = url_params

        if flag == 'repo':
            repos = repos.filter(name__icontains=keyword)
        elif flag == 'description':
            repos = repos.filter(desc__icontains=keyword)
        elif flag == 'author':
            repos = repos.filter(author__icontains=keyword)
        elif flag == 'all':
            repos = repos.filter(Q(name__icontains=keyword)|Q(desc__icontains=keyword)|Q(author__icontains=keyword))

        try:
            cur_page = int(request.args.get('page', 1))
        except:
            return 'page error', 404

        repos = repos.paginate(page=cur_page, per_page=PER_PAGE)
        data['repos'] = repos
        
        return render_template(self.template_name, **data)

    def post(self, collection_id):
        instance = CollectionDetailEditView()
        return instance.post(collection_id)

class ReposView(MethodView):
    decorators = [login_required, admin_permission.require(401),]
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

        data = { 'repos':repos, 'languages':languages.value_list if languages else [], 'cur_language':cur_language, 
            'url_params':url_params }

        data['language_cursor'] = language_cursor
         
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

    def add_repos_to_collections(self, repos, collection):

        repos_list = [ {'id':repo.id, 'link':repo.link, 'full_name':repo.full_name, 'desc':repo.desc, 'language':repo.language } for repo in repos]

        collection.modify(push_all__repos=repos_list)
        collection.modify(set__last_update=datetime.now())


    def star_repos(self, repos):
        for repo in repos:
            repo.modify(add_to_set__starred_users=current_user.username)

