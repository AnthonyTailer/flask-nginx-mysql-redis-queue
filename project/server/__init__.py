# project/server/__init__.py


import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_restful import Api

# instantiate the extensions
bootstrap = Bootstrap()


# def response_not_found(e):
#     return jsonify({
#         'message': '404 Not Found, chap, you made a mistake typing that URL',
#         'error': print(e)
#     }), 404
#
#
# def response_forbidden(e):
#     return jsonify({
#         'message': '403 Forbidden, you do not have permission to this URL',
#         'error': print(e)
#     }), 403
#
#
# def response_internal_server_error(e):
#     return jsonify({
#         'message': '500 internal server error, something went wrong :/',
#         'error': print(e)
#     }), 500


def create_app(script_info=None):
    # instantiate the app
    app = Flask(
        __name__,
        template_folder='../client/templates',
        static_folder='../client/static'
    )
    api = Api(app)

    # set error handling
    # app.register_error_handler(404, response_not_found)
    # app.register_error_handler(403, response_forbidden)
    # app.register_error_handler(500, response_internal_server_error)

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    app.config.from_object(app_settings)

    # set up extensions
    bootstrap.init_app(app)

    # register blueprints
    from project.server.main.views.views import main_blueprint
    app.register_blueprint(main_blueprint)

    # shell context for flask cli
    app.shell_context_processor({'app': app})

    # set API routes
    from project.server.main.views import views
    from project.server.main.resources import User as UserResources, Audio, Task
    from project.server.main.models import User

    # User routes
    api.add_resource(UserResources.UserRegistration, '/api/registration')
    api.add_resource(UserResources.UserLogin, '/api/login')
    api.add_resource(UserResources.UserLogoutAccess, '/api/logout/access')
    api.add_resource(UserResources.UserLogoutRefresh, '/api/logout/refresh')
    api.add_resource(UserResources.TokenRefresh, '/api/token/refresh')
    api.add_resource(UserResources.AllUsers, '/api/users')
    api.add_resource(UserResources.SecretResource, '/api/secret')

    # Tasks routes
    api.add_resource(Task.TaskStatus, '/api/task')

    # Audio routes
    api.add_resource(Audio.AudioTranscription, '/api/audio/transcription')

    return app
