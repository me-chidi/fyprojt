from unittest.mock import MagicMock, patch
import pytest
from myapp.models import User
import flask_login


hashed_password = "hashed-password"
data = {"username": "admin", "password": hashed_password}
node_data = {"node_id": "1", "to_serial": "atv", "status": "ON"}
fake_serial = MagicMock()


@pytest.fixture()
def authenticated_request(app):
    with app.test_request_context():
        # Directly logs in a user.
        user = User.query.filter_by(id=1).first()

        yield flask_login.login_user(user)

        # necessary to remove the current user from the
        # login manager so as not to interfere with other tests
        flask_login.logout_user()


class TestRegister:
    def test_user_does_not_exist_and_isnot_loggedin(self, client):
        response = client.post("/register", data=data)
        assert response.status_code == 200

    def test_user_already_exists_and_is_loggedin(self, client, authenticated_request):
        response = client.get("/register")
        assert b"<h3>Register To Login...</h3>" not in response.data

    def test_user_already_exists_and_isnot_loggedin(self, client, app):
        with client:
            response = client.post("/register", data=data)
            assert b"Username already exists!" in response.data
        with app.app_context():
            assert User.query.filter_by(username="admin").count() == 1


class TestLogin:
    def test_user_isnot_loggedin_and_attempts_login(self, client):
        with client:
            client.post("/", data=data)
            response = client.get("/dashboard")
            assert b"<h3>Welcome to Zigbee Street Light Control Panel!</h3>" not in response.data

    def test_user_is_loggedin_and_attempts_login(self, client, authenticated_request):
        with client:
            client.post("/", data=data)
            response = client.get("/")
            assert b"<h3>Welcome to Zigbee Street Light Control Panel!</h3>" not in response.data


class TestLogout:
    def test_logout_when_user_isnot_loggedin(self, client):
        response = client.get("/logout")
        assert b"zDashboard" not in response.data

    def test_logout_when_user_is_loggedin(self, client, authenticated_request):
        response = client.get("/logout")
        assert b"zDashboard" not in response.data


class TestUpdate:
    def test_accessing_update_without_id_returns404(self, client):
        response = client.post("/update")
        assert response.status_code == 404

    # Necessary to mock the serial object
    # because the pyserial module has unexpected behaviour attimes
    def test_update_when_user_is_loggedin_valid_data_arduino_connected(
        self, client, authenticated_request
    ):
        with (
            patch("pyduino.serial_connection", fake_serial),
            patch("pyduino.serial_connection.is_open", return_value=True),
            patch("pyduino.serial_connection.write"),
        ):
            response = client.post("/update/1", json=node_data)
            assert "success" in response.json
            assert response.status_code == 200

    def test_update_when_user_is_loggedin_valid_data_arduino_disconnected(
        self, client, authenticated_request
    ):
        response = client.post("/update/1", json=node_data)
        assert "error" in response.json
        assert response.status_code == 500

    def test_update_when_user_is_loggedin_invalid_data_arduino_connected(
        self, client, authenticated_request
    ):
        response = client.post("/update/1", json={})
        assert "error" in response.json
        assert response.status_code == 400

    def test_update_when_user_is_not_loggedin_valid_data_arduino_connected(self, client):
        response = client.get("/update/1")
        assert b"Method Not Allowed" in response.data
        assert response.status_code == 405


class TestUpdateAll:
    def test_update_all_when_user_is_not_loggedin_valid_data_arduino_connected(self, client):
        response = client.get("/update_all")
        assert b"Method Not Allowed" in response.data
        assert response.status_code == 405

    def test_update_all_when_user_is_loggedin_valid_data_arduino_connected(
        self, client, authenticated_request
    ):
        with (
            patch("pyduino.serial_connection", fake_serial),
            patch("pyduino.serial_connection.is_open", return_value=True),
            patch("pyduino.serial_connection.write"),
        ):
            response = client.post("/update_all", json={"status": "ON"})
            assert "success" in response.json
            assert response.status_code == 200

    def test_update_all_when_user_is_loggedin_valid_data_arduino_disconnected(
        self, client, authenticated_request
    ):
        response = client.post("/update_all", json={"status": "ON"})
        assert "error" in response.json
        assert response.status_code == 500

    def test_update_all_when_user_is_loggedin_invalid_data_arduino_connected(
        self, client, authenticated_request
    ):
        response = client.post("/update_all", json={})
        assert "error" in response.json
        assert response.status_code == 400


class TestDashboard:
    def test_dashboard_when_user_loggedin_returns_stat_table(self, client, authenticated_request):
        response = client.get("/dashboard")
        assert b"LDR-resistance[higher=less light]" in response.data

    def test_dashboard_when_user_not_loggedin(self, client):
        response = client.get("/dashboard")
        assert b"LDR-resistance[higher=less light]" not in response.data

    def test_dashboard_with_POST_returns_405(self, client):
        response = client.post("/dashboard", data={})
        assert response.status_code == 405
