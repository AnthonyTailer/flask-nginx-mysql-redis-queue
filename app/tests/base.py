# app/server/tests/base.py


from flask_testing import TestCase

from app.main import app

app = app()


class BaseTestCase(TestCase):

    def create_app(self):
        app.config.from_object('app.server.config.TestingConfig')
        return app

    def setUp(self):
        pass

    def tearDown(self):
        pass
