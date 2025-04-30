from myapp import db
from flask_login import UserMixin


# DB models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)


class Nodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(5), nullable=False)
    battery_lvl = db.Column(db.Integer, nullable=False)
    ldr_res = db.Column(db.Integer, nullable=False)
