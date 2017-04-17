#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_admin import AdminIndexView
from flask_login import current_user

from .admin import register_admin_views

# Create customized index view class
class GeneralAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_superuser