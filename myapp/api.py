from flask_login import (
    login_required,
    current_user,
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
)
from flask import Flask, Blueprint, request, redirect, url_for, render_template, jsonify, session
from myapp.forms import LoginForm, RegisterForm
from myapp.models import User, Nodes
from myapp import bcrypt, db, login_manager
import pyduino as pyd

api = Blueprint('api', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# logs the user out after 10 minutes
# @app.before_request
# def make_session_permanent():
#     session.permanent = True
#     app.permanent_session_lifetime = timedelta(minutes=10)


@api.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated: # prevents user from accessing login page when logged in
        return redirect(url_for("api.api.dashboard"))
    fail = False
    form = LoginForm()
    if form.validate_on_submit():
        # logs in if user and password exist
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("api.api.dashboard"))
            else:
                fail = True
        else:
            fail = True
    return render_template("index.html", form=form, fail=fail)


@api.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("api.api.dashboard"))
    duplicate = False
    fail = False
    form = RegisterForm()

    if form.validate_on_submit():
        # logic to prevent duplicate users
        if User.query.filter_by(username=form.username.data).first():
            duplicate = True
        else:
            hashed_pwd = bcrypt.generate_password_hash(form.password.data)
            user = User(username=form.username.data, password=hashed_pwd)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for("api.api.index"))
            except:
                fail = True
    return render_template("register.html", form=form, fail=fail, duplicate=duplicate)


@api.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@api.route("/update/<int:id>", methods=["POST"])
@login_required
def update(id):
    # Parse JSON from the request body
    data = request.get_json()
    if not data or "node_id" not in data:
        return jsonify({"error": "Invalid data"}), 400

    node = Nodes.query.get_or_404(id)
    to_serial = f"{data['to_serial']}{id}\n"
    try:
        # Send data to Arduino
        if pyd.serial_connection and pyd.serial_connection.is_open:
            pyd.serial_connection.write(to_serial.encode("utf-8"))
            return (
                jsonify(
                    {
                        "success": f"Node {node.id} turn {data['status']} request sent to Arduino"
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Serial connection not available"}), 500
    except Exception as e:
        return jsonify({"error": f"Error updating node {node.id}: {e}"}), 500


@api.route("/update_all", methods=["POST"])
@login_required
def update_all():
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": 'Invalid or missing "status" key'}), 400

    command = "atv" if data["status"] == "ON" else "dtv"
    nodes = Nodes.query.all()

    try:
        for node in nodes:
            to_serial = f"{command}{node.id}\n"
            if pyd.serial_connection and pyd.serial_connection.is_open:
                pyd.serial_connection.write(to_serial.encode("utf-8"))
            else:
                return jsonify({"error": "Serial connection not available"}), 500
    except Exception as e:
        return jsonify({"error": f"Error updating nodes: {e}"}), 500
    else:
        return (
            jsonify(
                {"success": f"All Nodes turn {data['status']} request sent to Arduino"}
            ),
            200,
        )


@api.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("api.api.index"))


@api.context_processor
def inject_nodes():
    nodes = Nodes.query.all()
    return {"nodes": nodes}