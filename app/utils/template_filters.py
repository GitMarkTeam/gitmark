#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus
from markupsafe import Markup

def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = quote_plus(s)
    return Markup(s)
