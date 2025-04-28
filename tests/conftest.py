import pytest
from wsgi import app as flaskapp


@pytest.fixture()
def app():
    app = flaskapp
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///testdb.db"
    app.config["WTF_CSRF_ENABLED"] = False  # prevents the forms from failing silently

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner


@pytest.fixture()
def monkeypatch():
    mpatch = pytest.MonkeyPatch()
    yield mpatch
    mpatch.undo()
