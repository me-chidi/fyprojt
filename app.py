import json
import os
from flask import Flask, request, redirect, url_for, render_template, jsonify
from flask_login import login_required, current_user, LoginManager, UserMixin, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)

app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = os.environ.get('FSKY')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


#DB models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class OperationalTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    on_time = db.Column(db.DateTime)
    off_time = db.Column(db.DateTime)


#forms
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)],
                           render_kw={'placeholder':'Username'})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)],
                             render_kw={'placeholder':'Password'})
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)],
                           render_kw={'placeholder':'Username'})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)],
                             render_kw={'placeholder':'Password'})
    submit = SubmitField('Login')




@app.route('/', methods=['GET','POST'])
def index():
    form = LoginForm()
    return render_template('index.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pwd)
        try:
            db.session.add(user)
            db.session.commit()
        except:
            return 'There was an error adding that user.'
    return render_template('register.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    #monitring stuff here
    return render_template('dashboard.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))