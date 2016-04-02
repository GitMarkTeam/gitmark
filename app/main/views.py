from flask import request, redirect, render_template, url_for, abort, flash
from flask import current_app, make_response
from flask.views import MethodView

from flask.ext.login import login_required, current_user

from . import models, tasks
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

        repos = repos.paginate(page=int(cur_page), per_page=PER_PAGE)

        data = { 'starred_repos':repos, 'languages':languages.value_list }
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
