# project/server/__init__.py
import json
from flask import Flask, make_response
from flask_bootstrap import Bootstrap
from flask_restful import Api
from project.server.main.resources import *
from project.server.main.models import *
from flask_jwt_extended import JWTManager

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('./project/server/logs/debug.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# instantiate the extensions
bootstrap = Bootstrap()


def create_app(script_info=None):
    # instantiate the app
    import os

    app = Flask(
        __name__,
        template_folder='../client/templates',
        static_folder='../client/static'
    )
    api = Api(app,  catch_all_404s=True)

    @api.representation('application/json')
    def output_json(data, code, headers=None):
        resp = make_response(json.dumps(data), code)
        resp.headers.extend(headers or {})
        return resp

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    app.config.from_object(app_settings)

    # set up extensions
    bootstrap.init_app(app)

    # register blueprints
    from project.server.main.views import main_blueprint
    app.register_blueprint(main_blueprint)

    # shell context for flask cli
    app.shell_context_processor({'app': app})

    # set JWT Authentication

    app.config['JWT_SECRET_KEY'] = UserModel.generate_hash('jwt-secret-string')

    jwt = JWTManager(app)

    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']

    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        jti = decrypted_token['jti']
        return RevokedTokenModel.is_jti_blacklisted(jti)

    # set API routes

    # User routes
    api.add_resource(UserRegistration, '/api/registration')
    api.add_resource(UserLogin, '/api/login')
    api.add_resource(UserLogoutAccess, '/api/logout')
    api.add_resource(AllUsers, '/api/users')
    api.add_resource(SecretResource, '/api/secret')

    # Word routes
    api.add_resource(Word, '/api/word/<word>')
    api.add_resource(WordRegistration, '/api/word') # get word and yours transcriptions

    # WordTranscription routes
    api.add_resource(WordTranscription, '/api/transcription/<transcription_id>')
    api.add_resource(WordTranscriptionRegistration, '/api/transcription')

    # Tasks routes
    api.add_resource(TaskStatus, '/api/task')

    # Audio routes
    api.add_resource(AudioTranscription, '/api/audio/transcription')

    return app
