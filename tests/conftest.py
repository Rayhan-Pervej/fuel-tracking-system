import pytest
import base64
import json
from unittest.mock import patch, MagicMock


def make_userinfo(user_id, role):
    payload = {"sub": user_id, "realm_access": {"roles": [role]}}
    return base64.b64encode(json.dumps(payload).encode()).decode()


@pytest.fixture
def app():
    with patch("app.extensions.mongo") as mock_mongo:
        mock_mongo.db = MagicMock()
        mock_mongo.db.__getitem__.return_value = MagicMock()

        with patch("app.extensions.socketio") as mock_socketio:
            mock_socketio.start_background_task = MagicMock()
            mock_socketio.init_app = MagicMock()
            mock_socketio.run = MagicMock()

            with patch("app._create_indexes"), \
                 patch("app.validate_config"):
                from app import create_app
                flask_app = create_app()
                flask_app.config["TESTING"] = True
                flask_app.config["MONGO_URI"] = "mongodb://localhost/test"
                yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(app):
    return make_userinfo("admin-1", "admin")

@pytest.fixture
def pump_admin_token(app):
    return make_userinfo("pump-admin-1", "employee")

@pytest.fixture
def employee_token(app):
    return make_userinfo("user-2", "employee")
