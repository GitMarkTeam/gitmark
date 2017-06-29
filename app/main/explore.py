#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import request, redirect, render_template, url_for, abort, flash, session, jsonify
from flask import current_app, make_response
from flask.views import MethodView

from flask_login import login_required, current_user
# from mongoengine.queryset.visitor import Q

from . import models
from gitmark.config import GitmarkSettings

class ExploreCollectionView(MethodView):
    template_name = 'main/explore_collection.html'
    def get(self):
        data = {}
        collections = models.Collection.objects(is_private=False)
        recent_collections = collections.order_by('-last_update')[:20]
        data['recent_collections'] = recent_collections

        most_followed_collections = collections.order_by('-follower_count')[:20]
        data['most_followed_collections'] = most_followed_collections

        return render_template(self.template_name, **data)