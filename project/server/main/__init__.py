import json
from flask_jwt_extended import JWTManager
from flask import Flask, make_response
from redis import Redis
from flask_bootstrap import Bootstrap
from flask_restful import Api
import rq
from .resources import *


def create_app():
    # instantiate the app
    import os

    app = Flask(
        __name__,
        template_folder='../client/templates',
        static_folder='../client/static'
    )

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    app.config.from_object(app_settings)

    # set up extensions
    bootstrap = Bootstrap()
    bootstrap.init_app(app)

    # register blueprints
    from project.server.main.views import main_blueprint
    app.register_blueprint(main_blueprint)

    from .models import UserModel, WordModel, WordTranscriptionModel, \
        PatientModel, TaskModel, RevokedTokenModel, EvaluationModel
    # shell context for flask cli
    app.shell_context_processor({
        'app': app, 'User': UserModel, 'Word': WordModel, 'Transcription': WordTranscriptionModel,
        'Patient': PatientModel, 'Task': TaskModel, 'Evaluation': EvaluationModel,
    })

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('speech-tasks', connection=app.redis)

    # set JWT Authentication
    app.config['JWT_SECRET_KEY'] = UserModel.generate_hash('jwt-secret-string')

    jwt = JWTManager(app)

    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']

    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        jti = decrypted_token['jti']
        return RevokedTokenModel.is_jti_blacklisted(jti)

    api = Api(app, catch_all_404s=True)
    # User routes



    api.add_resource(UserRegistration, '/api/registration')

    # api.add_resource(UserLogin, '/api/login')
    #
    # api.add_resource(UserLogoutAccess, '/api/logout')
    # api.add_resource(User, '/api/user')  # GET and PUT
    # api.add_resource(UserResetPassword, '/api/user/change/password')
    #
    # # Patitent routes
    # api.add_resource(PatientRegistration, '/api/patient')
    # api.add_resource(Patient, '/api/patient/<patient_id>')
    # api.add_resource(PatientAll, '/api/patient/all')
    #
    # # Word routes
    # api.add_resource(WordRegistration, '/api/word')
    # api.add_resource(Word, '/api/word/<word>')  # PUT, DELETE and GET word and yours transcriptions
    # api.add_resource(WordAll, '/api/word/all')
    #
    # # WordTranscription routes
    # api.add_resource(WordTranscription, '/api/transcription/<transcription_id>')
    # api.add_resource(WordTranscriptionRegistration, '/api/transcription')
    #
    # # Evaluation Routes
    # api.add_resource(Evaluation, '/api/evaluation/<evaluation_id>')
    # api.add_resource(EvaluationRegistration, '/api/evaluation')
    #
    # # WordEvaluation
    # api.add_resource(WordEvaluationRegistration, '/api/evaluation/word')
    #
    # # Tasks routes
    # api.add_resource(TaskStatus, '/api/task/<task_id>')
    #
    # api.add_resource(SecretResource, '/api/secret')

    @api.representation('application/json')
    def output_json(data, code, headers=None):
        resp = make_response(json.dumps(data), code)
        resp.headers.extend(headers or {})
        return resp

    return app



