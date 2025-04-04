import json
import os
from threading import Thread
from time import sleep
import pyduino as pyd
from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from turbo_flask import Turbo
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
app.config['SERVER_NAME'] = '127.0.0.1' or 'localhost'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
turbo = Turbo(app)


def updater_thread():
    with app.app_context():
        while True:
            sleep(1.5)
            try:
                print('🔄 Sending TurboFlask update...')  # Debugging print
                turbo.push(turbo.update(render_template('stat-table.html'), 'table'))
            except Exception as e:
                print(f'❌ TurboFlask push failed: {e}')
        
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
# @app.before_request 
# def make_session_permanent():
#     session.permanent = True
#     app.permanent_session_lifetime = timedelta(minutes=10)


@app.route('/', methods=['GET','POST'])
def index():
    if current_user.is_authenticated:   #prevents user from accessing login page when logged in
        redirect(url_for('dashboard'))
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
    if current_user.is_authenticated:   #prevents user from accessing login page when logged in
        redirect(url_for('dashboard'))
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

@app.route('/dashboard')
@login_required
def dashboard():
    #reload the html table here every 2 seconds
    nodes = Nodes.query.all()
    return render_template('dashboard.html', nodes=nodes)

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    # Parse JSON from the request body
    data = request.get_json()
    if not data or 'node_id' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    node = Nodes.query.get_or_404(id)
    to_serial = f'{data['to_serial']}{id}\n'
    try:
        # Send data to Arduino
        if pyd.serial_connection and pyd.serial_connection.is_open:
            pyd.serial_connection.write(to_serial.encode('utf-8'))
            return jsonify({'success': f'Node {node.id} turn {data['status']} request sent to Arduino'}), 200
        else:
            return jsonify({'error': 'Serial connection not available'}), 500
    except Exception as e:
        return jsonify({'error': f'Error updating node {node.id}: {e}'}), 500
    
@app.route('/update_all', methods=['POST'])
@login_required
def update_all():
    # Get JSON data safely
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Invalid or missing "status" key'}), 400

    #if status ON 'atv' append looped node.id
    # Update all nodes
    command = 'atv' if data['status'] == 'ON' else 'dtv'
    nodes = Nodes.query.all()

    try:
        for node in nodes:
            to_serial = f'{command}{node.id}\n'
                # Send data to Arduino
            if pyd.serial_connection and pyd.serial_connection.is_open:
                pyd.serial_connection.write(to_serial.encode('utf-8'))  
        # the exception is not caught here for some reason 
            else:
                return jsonify({'error': 'Serial connection not available'}), 500
    except Exception as e:
        return jsonify({'error': f'Error updating nodes: {e}'}), 500
    else:
        return jsonify({'success': f'All Nodes turn {data['status']} request sent to Arduino'}), 200

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.context_processor
def inject_nodes():
    nodes = Nodes.query.all()
    return {'nodes': nodes}

try:
    pyduino_thread = Thread(target=pyd.start_pyduino, args=(db, Nodes, app), daemon=True)
    pyduino_thread.start()
    upthread = Thread(target=updater_thread, daemon=True)
    upthread.start()
except Exception as e:
    print(f'An error occurred.\nError: {e}')

# #start ngrok
# def start_ngrok():
#     from pyngrok import ngrok
#     url = ngrok.connect(5000)
#     print('Tunnel url:', url)

# if app.config['START_NGROK']:
#     start_ngrok()
