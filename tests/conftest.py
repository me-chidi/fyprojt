import pytest 
import functools
from flask.testing import FlaskClient
from wsgi import app as fapp
from decorator import decorator

@pytest.fixture()
def app():
    app = fapp
    app.config['TESTING'] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///testdb.db'

    # print('crete db')
    # with app.app_context():
    #     db.create_all()
        
    yield app

    # delete dummy db here

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner

@decorator
def force_login(func, username=None, *args, **kwargs):
    for arg in args:
        if isinstance(arg, FlaskClient):
            with arg:
                with arg.session_transaction() as sess:
                    sess['_user_id'] = username
            return func(*args, **kwargs)
    return func(*args, **kwargs)