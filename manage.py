# manage.py
# -*- coding: utf-8 -*-
import click
import redis
from flask.cli import FlaskGroup
from rq import Worker, Queue, Connection
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from database import Base
from project.server.main import create_app
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('./project/server/logs/debug.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# instantiate the extensions


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
@click.argument('option1')
@click.argument('option2', required=False)
def db(option1, option2):
    manager.run()


@cli.command()
def run_worker():
    redis_url = app.config['REDIS_URL']
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(map(Queue, app.config['QUEUES']))
        worker.work()


if __name__ == '__main__':
    cli()
