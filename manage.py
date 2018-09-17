# manage.py
# -*- coding: utf-8 -*-

import unittest
import click
import os

from flask.cli import FlaskGroup
from project.server import create_app

import redis
from rq import Connection, Worker
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from project.server.main.models import *

app = create_app()

migrate = Migrate()
migrate.init_app(app, Base)

cli = FlaskGroup(create_app=create_app)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

user = os.environ['MYSQL_USER']
pwd = os.environ['MYSQL_ROOT_PASSWORD']
db = os.environ['DB_NAME']
host = os.environ['MYSQL_HOST']
port = os.environ['DB_PORT']

db_uri = 'mysql://%s:%s@%s:%s/%s' % (user, pwd, host, port, db)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

@cli.command()
@click.argument('option')
def db(option):
    manager.run()


@cli.command()
def run_worker():
    redis_url = app.config['REDIS_URL']
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(app.config['QUEUES'])
        worker.work()


@cli.command()
def test():
    """Runs the unit tests without test coverage."""
    tests = unittest.TestLoader().discover('project/tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    cli()
