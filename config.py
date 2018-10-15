# app/server/config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))
from dotenv import load_dotenv

load_dotenv(os.path.join(basedir, '.env'))


class BaseConfig(object):
    """Base configuration."""
    WTF_CSRF_ENABLED = True
    REDIS_URL = 'redis://'
    QUEUES = ['high', 'default', 'low']
    UPLOAD_FOLDER = './app/audios'
    ALLOWED_EXTENSIONS = {'wav'}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    user = os.environ['MYSQL_USER']
    pwd = os.environ['MYSQL_ROOT_PASSWORD']
    db = os.environ['DB_NAME']
    host = os.environ['MYSQL_HOST']
    port = os.environ['DB_PORT']
    db_uri = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (user, pwd, host, port, db)
    os.environ.setdefault('DATABASE_URL', db_uri)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    FLASK_SKIP_DOTENV = 1
    FLASK_DEBUG = 1


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    WTF_CSRF_ENABLED = False
    # PRESERVE_CONTEXT_ON_EXCEPTION = False


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    # PRESERVE_CONTEXT_ON_EXCEPTION = False
