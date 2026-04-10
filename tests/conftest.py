import pytest
from unittest.mock import patch, MagicMock
import jwt

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
                flask_app.config["JWT_SECRET_KEY"] = "test-secret"
                flask_app.config["MONGO_URI"] = "mongodb://localhost/test"
                yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(app):
    return jwt.encode({"user_id": "admin-1", "role": "admin"}, app.config["JWT_SECRET_KEY"], algorithm="HS256")

@pytest.fixture
def pump_admin_token(app):
    return jwt.encode({"user_id": "pump-admin-1", "role": "employee"}, app.config["JWT_SECRET_KEY"], algorithm="HS256")

@pytest.fixture
def employee_token(app):
    return jwt.encode({"user_id": "user-2", "role": "employee"}, app.config["JWT_SECRET_KEY"], algorithm="HS256")

