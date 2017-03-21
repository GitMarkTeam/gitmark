#!/usr/bin/env python

from gitmark import create_app, celery_app


app = create_app()
app.app_context().push()
