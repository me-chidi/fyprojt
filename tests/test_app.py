import pytest
from sqlite3 import IntegrityError
from myapp.models import User, db
from tests.conftest import force_login


#use a testdb bro

data = {'username': 'admin', 'password': 'hashed-password'}
node_data = {"node_id": "1", "to_serial": "atv", "status": "ON"}

class TestRegister():
    def test_user_does_not_exist_and_isnot_loggedin(self, client):
        response = client.post('/register', data=data)                
        assert response.status_code == 200

    @pytest.mark.skip 
    @force_login(username=1)
    def test_user_already_exists_and_is_loggedin(self, client):
        response = client.get('/register')
        assert b'<h3>Register To Login...</h3>' not in response.data

    @pytest.mark.skip 
    def test_user_already_exists_and_isnot_loggedin(self, client, app):
        with app.app_context():
            user = User(username='admin', password='hashed-password')
            db.session.add(user)
            db.session.commit()
        response = client.post('/register', data=data)
        assert b'Username already exists!' in response.data
        with app.app_context():
            assert User.query.filter_by(username='admin').count() == 1

        
class TestLogin:
    def test_user_isnot_loggedin_and_attempts_login(self, client):
        with client:
            client.post('/', data=data)
            response = client.get('/dashboard')
            assert b'<h3>Welcome to Zigbee Street Light Control Panel!</h3>' not in response.data

    @pytest.mark.skip 
    @force_login(username=1)
    def test_user_is_loggedin_and_attempts_login(self, client):
        with client:
            client.post('/', data=data)
            response = client.get('/')
            assert b'<h3>Welcome to Zigbee Street Light Control Panel!</h3>' not in response.data

    
class TestLogout:
    def test_logout_when_user_isnot_loggedin(self, client):
        response = client.get('/logout')
        assert b'zDashboard' not in response.data

    @force_login(username=1)
    def test_logout_when_user_is_loggedin(self, client):
        response = client.get('/logout')
        assert b'zDashboard' not in response.data


class TestUpdate:
    def test_accessing_update_without_id_returns404(self, client):
        response = client.post('/update')
        assert response.status_code == 404
    
    @force_login(username=1)
    def test_update_when_user_is_loggedin_valid_data_arduino_connected(self, client):
        response = client.post('/update/1', json=node_data)
        assert 'success' in response.json
        assert response.status_code == 200

    @force_login(username=1)
    def test_update_when_user_is_loggedin_valid_data_arduino_disconnected(self, client):
        response = client.post('/update/1', json=node_data)
        assert 'error' in response.json
        assert response.status_code == 500

    @force_login(username=1)
    def test_update_when_user_is_loggedin_invalid_data_arduino_connected(self, client):
        response = client.post('/update/1', json={})
        assert 'error' in response.json
        assert response.status_code == 400

    def test_update_when_user_is_not_loggedin_valid_data_arduino_connected(self, client):
        response = client.get('/update/1')
        assert b'Method Not Allowed' in response.data
        assert response.status_code == 405


class TestUpdateAll:
    def test_update_all_when_user_is_not_loggedin_valid_data_arduino_connected(self, client):
        response = client.get('/update_all')
        assert b'Method Not Allowed' in response.data
        assert response.status_code == 405

    @force_login(username=1)
    def test_update_all_when_user_is_loggedin_valid_data_arduino_connected(self, client):
        response = client.post('/update_all', json={"status": "ON"})
        assert 'success' in response.json
        assert response.status_code == 200

    @force_login(username=1)
    def test_update_all_when_user_is_loggedin_valid_data_arduino_disconnected(self, client):
        response = client.post('/update_all', json={"status": "ON"})
        assert 'error' in response.json
        assert response.status_code == 500

    @force_login(username=1)
    def test_update_all_when_user_is_loggedin_invalid_data_arduino_connected(self, client):
        response = client.post('/update_all', json={})
        assert 'error' in response.json
        assert response.status_code == 400


class TestDashboard:
    @force_login(username=1)
    def test_dashboard_when_user_loggedin_returns_stat_table(self, client):
        response = client.get('/dashboard')
        assert b'LDR-resistance[higher=less light]' in response.data

    # the problem with force login is that it keeps the session alive for each fxn so 
    # setting it as a fixture should stop that
    def test_dashboard_when_user_not_loggedin(self, client):
        response = client.get('/dashboard')
        assert b'LDR-resistance[higher=less light]' not in response.data

    def test_dashboard_with_POST_returns_405(self, client):
        response = client.post('/dashboard', data={})
        assert response.status_code == 405


