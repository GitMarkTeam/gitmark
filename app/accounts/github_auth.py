#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, datetime

# from django.http import HttpResponse, Http404
# from django.shortcuts import render, redirect
# from django.core.urlresolvers import reverse
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
# from django.contrib import messages
# from django.conf import settings
from flask import render_template, redirect, request, flash, url_for, current_app, session
from flask.ext.login import login_user, current_user

import requests
from requests_oauthlib import OAuth2Session, OAuth2

from gitmark import github_apis, config
from gitmark.config import GitmarkSettings
from utils.wrap_qiniu import qiniu_fetch_img
from . import models

client_id = GitmarkSettings['github']['client_id']
client_secret = GitmarkSettings['github']['client_secret']
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'

def github_auth():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    github = OAuth2Session(client_id)
    authorization_url, state = github.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_user_state'] = state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.


def github_callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    github = OAuth2Session(client_id, state=session['oauth_user_state'])
    token = github.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_user_token'] = token

    # response to callback as follow:
    if session['oauth_callback_type'] == 'register':
        return github_register_behavior()

    if session['oauth_callback_type'] == 'login':
        return github_login_behavior()

    if session['oauth_callback_type'] == 'link_github':
        return github_link_account_behavior()

    if session['oauth_callback_type'] == 'reset_password':
        return github_auth_user_behavior()

    url = url_for('main:index')
    return redirect(url)

def github_register_behavior():
    url = github_apis.auth_user()
    auth = OAuth2(client_id=client_id, token=session['oauth_user_token'])
    res = requests.get(url, auth=auth)
    if res.status_code != 200:
        msg = 'GitHub authorization failed'
        url = url_for('accounts.register')
        # messages.add_message(request, messages.ERROR, msg)
        flash(msg, 'danger')
        return redirect(url)

    github_user = res.json()
    username = github_user.get('login')
    email = github_user.get('email')
    print 'email: {0}'.format(email)
    github_url = github_user.get('html_url')
    github_avatar_url = github_user.get('avatar_url')

    users = models.User.objects.filter(github_username=username)
    if len(users) > 0:
        msg = 'You have registered with Github'
        # messages.add_message(request, messages.ERROR, msg)
        flash(msg, 'danger')
        url = url_for('accounts.login')
        return redirect(url)

    def get_unique_username(username):
        check_username = username
        while True:
            users = models.User.objects.filter(username=check_username)
            if len(users) == 0:
                return check_username
            check_username = check_username + str(randint(1, 1000))

    # def create_user(username):
    #     # try:
    #     #     user = models.User()
    #     #     user.username = username
    #     #     user.password = 'password'

    #     #     user.save()

    #     #     return user

    #     # except:
    #     #     from random import random, randint
    #     #     username = username + str(randint(1, 1000))
    #     #     # return create_user(username)
    #     #     return None
    #     user = models.User()
    #     user.username = username
    #     user.password = 'password'

    #     user.save()

    #     return user

    avatar_name = 'github_avatar_{0}.jpeg'.format(username)
    avatar_url = qiniu_fetch_img(github_avatar_url, avatar_name)
    checked_username = get_unique_username(username)

    user = models.User()
    user.username = checked_username
    user.password = str(datetime.datetime.now)
    user.email = email
    user.github_username = username
    user.github = github_url
    user.is_email_confirmed = True
    user.avatar_url = avatar_url
    user.save()

    login_user(user)
    user.last_login = datetime.datetime.now
    user.save()

    url = url_for('accounts.login')
    return redirect(url)

def github_login_behavior():
    url = github_apis.auth_user()
    auth = OAuth2(client_id=client_id, token=session['oauth_user_token'])
    res = requests.get(url, auth=auth)
    if res.status_code != 200:
        msg = 'GitHub authorization failed'
        url = url_for('accounts.register')
        flash(msg, 'danger')
        return redirect(url)

    github_user = res.json()
    username = github_user.get('login')
    # email = github_user.get('email')
    # github_url = github_user.get('html_url')
    # github_avatar_url = github_user.get('avatar_url')

    try:
        user = models.User.objects.get(github_username=username)
    except models.User.DoesNotExist:
        msg = 'Please register first'
        flash(msg, 'danger')
        return redirect(url_for('accounts.register'))

    login_user(user)
    user.last_login = datetime.datetime.now
    user.save()

    url = url_for('accounts.login')
    return redirect(url)

def github_link_account_behavior():
    url = github_apis.auth_user()
    auth = OAuth2(client_id=client_id, token=session['oauth_user_token'])
    res = requests.get(url, auth=auth)
    if res.status_code != 200:
        msg = 'GitHub authorization failed'
        flash(msg, 'danger')
        return redirect(url_for('main.index'))

    github_user = res.json()
    username = github_user.get('login')
    email = github_user.get('email')
    github_url = github_user.get('html_url')
    github_avatar_url = github_user.get('avatar_url')

    if not current_user.avatar_url:
        avatar_name = 'github_avatar_{0}.jpeg'.format(username)
        avatar_url = qiniu_fetch_img(github_avatar_url, avatar_name)
        current_user.avatar_url = avatar_url

    current_user.github_username = username
    current_user.github = github_url
    
    current_user.save()

    return redirect(url_for('main.index'))

def github_auth_user_behavior():
    url = github_apis.auth_user()
    auth = OAuth2(client_id=client_id, token=session['oauth_user_token'])
    res = requests.get(url, auth=auth)
    if res.status_code != 200:
        msg = 'GitHub authorization failed'
        url = url_for('accounts.register')
        flash(msg, 'danger')
        return False

    return True

