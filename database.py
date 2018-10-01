import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

user = os.environ['MYSQL_USER']
pwd = os.environ['MYSQL_ROOT_PASSWORD']
db = os.environ['DB_NAME']
host = os.environ['MYSQL_HOST']
port = os.environ['DB_PORT']

db_uri = 'mysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (user, pwd, host, port, db)

engine = create_engine(db_uri, echo=True)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()

    Base.metadata.create_all(bind=engine)
