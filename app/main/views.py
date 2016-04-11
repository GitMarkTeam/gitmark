from flask import request, redirect, render_template, url_for, abort, flash
from flask import current_app, make_response
from flask.views import MethodView

from flask.ext.login import login_required, current_user

from . import models, tasks, forms
from gitmark.config import GitmarkSettings

PER_PAGE = GitmarkSettings['pagination']['per_page']

def hello():
    return 'hello, world'

def index():
    # return 'index'
    return render_template('main/index.html')

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
            collections = collections = models.Collection.objects(owner=current_user.username)
            data['collections'] = collections

        return render_template(self.template_name, **data)



