import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    with patch("app.extensions.mongo") as mock_mongo:
        mock_mongo.db = MagicMock()
        mock_mongo.db.__getitem__.return_value = MagicMock()

        with patch("app.extensions.socketio") as mock_socketio:
            mock_socketio.start_background_task = MagicMock()
            mock_socketio.init_app = MagicMock()
            mock_socketio.run = MagicMock()

            with patch("app.__init__._create_indexes"):
                from app import create_app
                flask_app = create_app()
                flask_app.config["TESTING"] = True
                flask_app.config["MONGO_URI"] = "mongodb://localhost/test"
                yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
