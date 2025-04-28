import config
from flask import Flask
from turbo_flask import Turbo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
turbo = Turbo()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.app_context().push()
    app.config.from_object(config)

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    turbo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "api.index"

    from myapp.api import api as api_blueprint

    app.register_blueprint(api_blueprint)

    return app


from myapp.models import User, Nodes  # noqa
from myapp.forms import LoginForm, RegisterForm  # noqa
from myapp import api  # noqa
