import os
import rq
import logging
from redis import Redis
import rq_dashboard
from flask import Flask
from config import BaseConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging.handlers import RotatingFileHandler
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()


def create_app(config_class=BaseConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('api-tasks', connection=app.redis)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/debug.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Speech API startup')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")




    # # Patitent routes
    # api.add_resource(resources.PatientRegistration, '/api/patient')
    # api.add_resource(resources.PatientResource, '/api/patient/<patient_id>')
    # api.add_resource(resources.PatientAll, '/api/patient/all')
    #
    # # Word routes
    # api.add_resource(resources.WordRegistration, '/api/word')
    # api.add_resource(resources.WordResource, '/api/word/<word>')  # PUT, DELETE and GET word and yours transcriptions
    # api.add_resource(resources.WordAll, '/api/word/all')
    #
    # # WordTranscription routes
    # api.add_resource(resources.WordTranscriptionResource, '/api/transcription/<transcription_id>')
    # api.add_resource(resources.WordTranscriptionRegistration, '/api/transcription')
    #
    # # Evaluation Routes
    # api.add_resource(resources.EvaluationResource, '/api/evaluation/<evaluation_id>')
    # api.add_resource(resources.EvaluationRegistration, '/api/evaluation')
    #
    # # WordEvaluation
    # api.add_resource(resources.WordEvaluationRegistration, '/api/evaluation/word')
    #
    # # Tasks routes
    # api.add_resource(resources.TaskStatus, '/api/task/<task_id>')

    # api.add_resource(resources.SecretResource, '/api/secret')

    return app


from app import models, helpers
