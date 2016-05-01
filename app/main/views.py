#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from flask import request, redirect, render_template, url_for, abort, flash, session
from flask import current_app, make_response
from flask.views import MethodView

from flask.ext.login import login_required, current_user
from mongoengine.queryset.visitor import Q

from . import models, tasks, forms
from gitmark.config import GitmarkSettings
from accounts import github_auth

PER_PAGE = GitmarkSettings['pagination']['per_page']

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
        return render_template(self.template_name)

    def post(self):
        if request.form.get('link_github'):
            session['oauth_callback_type'] = 'link_github'           
            return github_auth.github_auth()
        
        elif request.form.get('rm_github'):
            current_user.github_username = ''
            # current_user.github = ''
            current_user.save()

        
        return redirect(url_for('main.index')) 

class StarredRepoView(MethodView):
    decorators = [login_required, ]
    template_name = 'main/starred_repo.html'

    def get(self):
        repos = models.Repo.objects(starred_users=current_user.username)
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

            collection.save()

            return redirect(url_for('main.my_collections'))

        return self.get(form=form)


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

        collection.name = name
        collection.description = description

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

        if collection.owner == current_user.username:
            collections = models.Collection.objects(owner=current_user.username)
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
            url_parm = '?keyword={0}&flag={1}'.format(keyword, flag)
            data['url_parm'] = url_parm

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
    decorators = [login_required, ]
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

        data = { 'repos':repos, 'languages':languages.value_list, 'cur_language':cur_language, 
            'url_params':url_params }

        data['language_cursor'] = language_cursor
         
        return render_template(self.template_name, **data)

