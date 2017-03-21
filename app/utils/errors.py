from flask import render_template


def handle_bad_request(e):
    return 'bad request!', 400

def handle_forbidden(e):
    # return 'request forbidden', 403
    return render_template('misc/403.html', msg=e.description), 403

def handle_unauthorized(e):
    # return 'request forbidden', 403
    return render_template('misc/401.html'), 401

def page_not_found(e):
    # return render_template('404.html'), 404
    # return 'admin 404 page', 404
    return render_template('misc/404.html', msg=e.description), 404