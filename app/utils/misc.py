#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import current_app, render_template
from flask_mail import Message
from gitmark import mail

def send_user_confirm_mail(to, user, token):
    title = 'GitMark confirm user email'
    msg = Message(title)
    msg.sender = current_app._get_current_object().config['MAIL_USERNAME']
    msg.recipients = [to]

    template_name = 'misc/confirm.txt'

    msg.body = render_template(template_name, user=user, token=token)
    msg.html = render_template(template_name, user=user, token=token)
        
    mail.send(msg)
