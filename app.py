import json
import os
from config import njson
from flask import Flask, request, redirect, url_for, render_template, jsonify
from flask_login import login_required, current_user, LoginManager, UserMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
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
#migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#DB models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class OperationalTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    on_time = db.Column(db.DateTime)
    off_time = db.Column(db.DateTime)

class Nodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(5), nullable=False)
    mode = db.Column(db.String(5), nullable=False)


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
    fail = False
    if form.validate_on_submit():
        #logs in if user and password exist
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                fail = True    
        else:
            fail = True
    return render_template('index.html', form=form, fail=fail)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    fail = False
    #create logic to prevent duplicate users 
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pwd)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))
        except:
            fail = True
    return render_template('register.html', form=form, fail=fail)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
 
    if request.method == 'POST':
    #monitring stuff here
        return redirect(url_for('dashboard'))
    else:
        #get the nodes:: called only once
        for node_data in njson['nodes']:
            node_id = int(node_data[0])
            status = node_data[1]
            mode = node_data[2]
            node = Nodes.query.get(node_id)
        
            #if node exists already then update
            if node:
                node.status = status
                node.mode = mode
                try:
                    db.session.commit() 
                except:
                    return f'There was an error adding node{node_id}'
            else:
                node = Nodes(status=status, mode=mode)
                try:
                    db.session.add(node)
                    db.session.commit() 
                except:
                    return f'There was an error adding node{node_id}'
        nodes = Nodes.query.all()
        return render_template('dashboard.html', nodes=nodes)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    #called from turn off/on form
    #single update
    node = Nodes.query.get_or_404(id)
    node.status = request.form['node_id']
    try:
        db.session.commit() 
    except:
        return f'There was an error updating node{node.id}'
    return redirect(url_for('dashboard'))
    
@app.route('/update_all', methods=['GET', 'POST'])
def update_all():
    #multiple update
    if request.method == 'POST':
        nodes = Nodes.query.all()
        for node in nodes:
            node.status = request.form['value']
        try:
            db.session.commit() 
        except:
            return 'There was an error updating nodes' 
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))