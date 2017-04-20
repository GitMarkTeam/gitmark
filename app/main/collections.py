#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json, os, io, sys

import requests

from flask import request, redirect, render_template, url_for, abort, flash, session, jsonify
from flask import current_app, make_response, send_from_directory
from flask.views import MethodView

from flask_login import login_required, current_user

from . import models, tasks, forms
from gitmark.config import GitmarkSettings
from gitmark import github_apis
from accounts import github_auth
from accounts.permissions import admin_permission
from accounts import models as accounts_models

PER_PAGE = GitmarkSettings['pagination']['per_page']
app_user = GitmarkSettings['github']['app_user']
app_pass = GitmarkSettings['github']['app_pass']



class MyCollectionsView(MethodView):
    decorators = [login_required]
    template_name = 'main/collections.html'

    def get(self, form=None, visibility=None):
        if not form:
            form = forms.CollectionForm()
        collections = models.Collection.objects(owner=current_user.username)
        if visibility == 'public':
            collections = collections.filter(is_private=False)
        if visibility == 'private':
            collections = collections.filter(is_private=True)

        tags = collections.distinct('tags')

        cur_tag = request.args.get('tag')
        if cur_tag:
            collections = collections.filter(tags=cur_tag)

        data = { 'collections':collections, 'form':form, 'tags': tags, 'cur_tag':cur_tag }

        return render_template(self.template_name, **data)

    def post(self, visibility=None):
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

    def get(self, username=None, following=False):
        if following:
            collections = models.Collection.objects(followers=current_user.username, is_private=False)
        else:
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
            collection.tags_str = ', '.join(collection.tags)
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
        tags_str = form.tags_str.data

        collection.name = name
        collection.description = description
        collection.is_private = is_private
        collection.tags = [ tag.strip() for tag in tags_str.split(',')] if tags_str else None

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
        if (not collection) or (collection.is_private and (current_user.is_anonymous or current_user.username!=collection.owner)):
            # return 'no collection', 404
            abort(404, 'No collection detail found')

        data = {'cur_collection': collection, 'collections':None}

        can_edit = False
        following = False

        if not current_user.is_anonymous and current_user.username == collection.owner:
            collections = models.Collection.objects(owner=collection.owner)
            can_edit = True
        else:
            collections = models.Collection.objects(owner=collection.owner, is_private=False)
            if not current_user.is_anonymous and current_user.username in collection.followers:
                following = True
        
        data['collections'] = collections
        data['can_edit'] = can_edit
        data['following'] = following

        return render_template(self.template_name, **data)

    def post(self, collection_id):
        if current_user.is_anonymous:
            msg = 'You need to login before follow the collection'
            flash(msg, 'warning')
            login_url = url_for('accounts.login')
            next_url = url_for('main.collection_detail', collection_id=collection_id)
            url = '{0}?next={1}'.format(login_url, next_url)
            return redirect(url)
        collection = models.Collection.objects.get_or_404(id=collection_id)
        if request.form.get('follow'):
            collection.modify(add_to_set__followers=current_user.username)
            msg = 'Succeed to follow this collection'
            
        elif request.form.get('unfollow'):
            collection.modify(unset__followers=current_user.username)
            msg = 'Succeed to unfollow this collection'
        elif request.form.get('export') and current_user.username==collection.owner:
            msg = 'Ready to export'
            if request.form.get('export-collection')=='json':
                msg = 'Ready to export as json'
                return self.export_as_json(collection)
            else:
                msg = 'Ready to export as markdown'
                return self.export_as_markdown(collection)
        flash(msg, 'success')
        return redirect(url_for('main.collection_detail', collection_id=collection_id))

    def delete(self, collection_id):
        collection = models.Collection.objects(owner=current_user.username, id=collection_id).first()

        if not collection:
            # return 'No collection found', 404
            abort(404, 'No collection found')

        collection.modify(pull_all__repos=collection.repos)
        collection.modify(set__last_update=datetime.now())

        if request.args.get('ajax'):
            return 'success'

        msg = 'Succeed to clear the collection'
        flash(msg, 'success')

        return redirect(url_for('main.my_collections'))

    def export_as_json(self, collection):
        data = collection.to_dict()
        # print(data, type(data))
        # return jsonify(data)
        export_path = current_app._get_current_object().config['EXPORT_PATH']
        file_name = '{0}-{1}.json'.format(collection.owner, collection.name)
        file_fullname = os.path.join(export_path, file_name)

        if sys.version_info < (3, 0):
            with io.open(file_fullname, 'w', encoding='utf-8') as f:
                # f.write(unicode(json.dumps(post_list, ensure_ascii=False, indent=4)))
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            with open(file_fullname, 'w') as fs:
                json.dump(data, fs, ensure_ascii=False, indent=4)

        return send_from_directory(export_path, file_name, as_attachment=True)

    def export_as_markdown(self, collection):
        data = collection.to_dict()
        export_path = current_app._get_current_object().config['EXPORT_PATH']
        file_name = '{0}-{1}.md'.format(collection.owner, collection.name)
        file_fullname = os.path.join(export_path, file_name)
        template_name = 'misc/export_collection.md'
        content = render_template(template_name, **data)

        with open(file_fullname, 'w') as fs:
            if sys.version_info < (3, 0):
                fs.write(content.encode('utf8'))
            else:
                fs.write(content)

        return send_from_directory(export_path, file_name, as_attachment=True)
        return content

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
