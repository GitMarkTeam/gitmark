#!/usr/bin/env python

# import os, sys
# sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask_script import Manager, Server

from gitmark import create_app

# manager = Manager(app)

# flask_app = GitmarkApp()
# flask_app.register_blueprint()
# manager = Manager(flask_app.app)

# app = create_app()
# manager = Manager(register_blueprint(app))

app = create_app()
# app.app_context().push()
manager = Manager(app)

# Turn on debugger by default and reloader
manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    host = '0.0.0.0',
    port = 5000)
)

if __name__ == "__main__":
    manager.run()