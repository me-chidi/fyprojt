import os


SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
SECRET_KEY = os.environ.get("FSKY") or "not-a-secret"
MAIN_PROC = os.environ.get("WERKZEUG_RUN_MAIN") != "true"
SERVER_NAME = "127.0.0.1" or "localhost"
START_NGROK = False  # change as needed
DEBUG = False
