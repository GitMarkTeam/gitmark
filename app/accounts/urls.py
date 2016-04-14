from flask import Blueprint

from . import views, github_auth
# from gitmark import app as accounts

accounts = Blueprint('accounts', __name__)

# accounts.add_url_rule('/login/', 'login', views.login, methods=['GET', 'POST'])
accounts.add_url_rule('/login/', view_func=views.LoginView.as_view('login'))
accounts.add_url_rule('/logout/', 'logout', views.logout)
# accounts.add_url_rule('/registration/', 'register', views.register, methods=['GET', 'POST'])
accounts.add_url_rule('/registration/', view_func=views.RegistrationView.as_view('register'))
accounts.add_url_rule('/registration/su/', view_func=views.RegistrationView.as_view('register_su'), defaults={'create_su':True})
# accounts.add_url_rule('/add-user/', 'add_user', views.add_user, methods=['GET', 'POST'])
accounts.add_url_rule('/users/', view_func=views.Users.as_view('users'))
accounts.add_url_rule('/users/edit/<username>', view_func=views.User.as_view('edit_user'))
# accounts.add_url_rule('/su-users/', view_func=views.SuUsers.as_view('su_users'))
# accounts.add_url_rule('/su-users/edit/<username>', view_func=views.SuUser.as_view('su_edit_user'))
accounts.add_url_rule('/user/settings/', view_func=views.Profile.as_view('settings'))
accounts.add_url_rule('/user/password/', view_func=views.Password.as_view('password'))


accounts.add_url_rule('/github/auth/', 'github_auth', github_auth.github_auth)
accounts.add_url_rule('/github/callback/', 'github_callback', github_auth.github_callback)