import json
import os
import threading
import pyduino as pyd
from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from flask_login import login_required, current_user, LoginManager, UserMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from datetime import timedelta, datetime

app = Flask(__name__)

app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = os.environ.get('FSKY') or 'not-a-secret'
app.config['START_NGROK'] = os.environ.get('START_NGROK') is not None and \
    os.environ.get('WERKZEUG_RUN_MAIN') 
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

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
    battery_lvl = db.Column(db.Integer, nullable=False)
    ldr_res = db.Column(db.Integer, nullable=False)
    

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

#logs the user out after 10 minutes
@app.before_request 
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)


serial_thread = threading.Thread(target=pyd.read_json_data, args=(pyd.connect_arduino(), db, Nodes, app.app_context()), daemon=True, )
serial_thread.start()

@app.route('/', methods=['GET','POST'])
def index():
    fail = False
    form = LoginForm()
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
    duplicate = False
    fail = False
    form = RegisterForm()

    if form.validate_on_submit():
        #logic to prevent duplicate users 
        if User.query.filter_by(username=form.username.data).first():
            duplicate = True
        else:
            hashed_pwd = bcrypt.generate_password_hash(form.password.data)
            user = User(username=form.username.data, password=hashed_pwd)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('index'))
            except:
                fail = True
    return render_template('register.html', form=form, fail=fail, duplicate=duplicate)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
    #monitring stuff here
        return redirect(url_for('dashboard'))
    else:
        nodes = Nodes.query.all()
        return render_template('dashboard.html', nodes=nodes)

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    # Parse JSON from the request body
    data = request.get_json()
    if not data or 'node_id' not in data:
        return jsonify({"error": "Invalid data"}), 400
    #instead of commit push to serial the read from serial 
    # makes sense
    #do the same for update all
    node = Nodes.query.get_or_404(id)
    node.status = data['status']
    try:
        db.session.commit()
        return jsonify({"success": f"Node {node.id} updated"}), 200
    
    except:
        return jsonify({"error": f"There was an error updating node {node.id}"}), 500
    
@app.route('/update_all', methods=['POST'])
@login_required
def update_all():
    try:
        # Get JSON data safely
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Invalid or missing 'status' key"}), 400

        # Update all nodes
        nodes = Nodes.query.all()
        for node in nodes:
            node.status = data['status']
        
        db.session.commit()
        return jsonify({"success": "All nodes updated"}), 200
    except Exception as e:
        print(f"Error updating all nodes: {e}")
        return jsonify({"error": "There was an error updating nodes"}), 500


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# #start ngrok
# def start_ngrok():
#     from pyngrok import ngrok
#     url = ngrok.connect(5000)
#     print('Tunnel url:', url)

# if app.config['START_NGROK']:
#     start_ngrok()
