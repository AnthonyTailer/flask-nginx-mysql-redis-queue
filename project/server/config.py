# project/server/config.py

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    """Base configuration."""
    WTF_CSRF_ENABLED = True
    REDIS_URL = 'redis://redis:6379/0'
    QUEUES = ['high', 'default', 'low']
    UPLOAD_FOLDER = './project/server/audios'
    ALLOWED_EXTENSIONS = {'wav'}
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
