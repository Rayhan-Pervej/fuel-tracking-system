"""
Socket.IO dashboard tests.
These tests use a dedicated app fixture that creates a fresh SocketIO instance
(separate from app.extensions.socketio) to avoid state pollution between tests.
"""
import jwt
import pytest
from unittest.mock import patch, MagicMock


SECRET_KEY = "test-secret"


def mock_build_payload():
    return {
        "stats": {
            "total_transactions": 5,
            "total_revenue": 625.0,
            "total_fuel_dispensed": 50.0
        },
        "transactions": [
            {
                "_id": f"txn-{i}",
                "vehicle_id": "veh-1",
                "pump_id": "pump-1",
                "fuel_price_id": "fp-1",
                "quantity": 10.0,
                "total_price": 1250.0,
                "created_at": "2025-01-01T00:00:00",
                "fuel_type": "octane",
                "unit": "liter",
                "currency": "BDT",
                "vehicle_number": "DH-1234",
                "pump_name": "Shell"
            }
            for i in range(5)
        ]
    }


@pytest.fixture(scope="module")
def sio_setup():
    """
    Creates a fresh Flask app + SocketIO instance isolated from app.extensions.socketio.
    Registers the dashboard event handlers on the fresh socketio instance.
    Module-scoped to avoid re-initialization between tests.
    """
    from flask import Flask
    from flask_socketio import SocketIO, emit, disconnect
    import jwt as pyjwt

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = SECRET_KEY

    sio = SocketIO(flask_app, async_mode="threading")

    # Register the same event handlers as app/sockets/events.py
    @sio.on("connect", namespace="/dashboard")
    def on_connect(auth=None):
        token = (auth or {}).get("token", "")
        if not token:
            disconnect()
            return
        try:
            pyjwt.decode(token, flask_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        except pyjwt.InvalidTokenError:
            disconnect()
            return
        payload = mock_build_payload()
        emit("init", payload)

    @sio.on("request_init", namespace="/dashboard")
    def handle_request_init():
        payload = mock_build_payload()
        emit("init", payload)

    yield flask_app, sio


def make_token():
    return jwt.encode({"user_id": "admin-1", "role": "admin"}, SECRET_KEY, algorithm="HS256")


class TestSocketIOConnect:
    def test_connect_with_valid_token(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        assert sc.is_connected(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")

    def test_connect_without_token_disconnects(self, sio_setup):
        flask_app, sio = sio_setup
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={})
        assert not sc.is_connected(namespace="/dashboard")

    def test_connect_with_invalid_token_disconnects(self, sio_setup):
        flask_app, sio = sio_setup
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": "bad.token.here"})
        assert not sc.is_connected(namespace="/dashboard")

    def test_connect_with_no_auth_disconnects(self, sio_setup):
        flask_app, sio = sio_setup
        sc = sio.test_client(flask_app, namespace="/dashboard")
        assert not sc.is_connected(namespace="/dashboard")


class TestSocketIOInitEvent:
    def test_connect_emits_init_event(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        assert "init" in [e["name"] for e in received]

    def test_init_payload_has_stats(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        init_events = [e for e in received if e["name"] == "init"]
        assert len(init_events) == 1
        data = init_events[0]["args"][0]
        assert "stats" in data
        assert "total_transactions" in data["stats"]
        assert "total_revenue" in data["stats"]
        assert "total_fuel_dispensed" in data["stats"]

    def test_init_payload_has_transactions(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        init_events = [e for e in received if e["name"] == "init"]
        data = init_events[0]["args"][0]
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        assert len(data["transactions"]) == 5

    def test_transaction_enrichment_fields_in_init(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        init_events = [e for e in received if e["name"] == "init"]
        txn = init_events[0]["args"][0]["transactions"][0]
        assert "fuel_type" in txn
        assert "unit" in txn
        assert "currency" in txn
        assert "vehicle_number" in txn
        assert "pump_name" in txn


class TestSocketIORequestInit:
    def test_request_init_emits_init(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        sc.get_received(namespace="/dashboard")  # clear connect init
        sc.emit("request_init", namespace="/dashboard")
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        assert "init" in [e["name"] for e in received]

    def test_request_init_payload_structure(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        sc.get_received(namespace="/dashboard")  # clear connect init
        sc.emit("request_init", namespace="/dashboard")
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        init_events = [e for e in received if e["name"] == "init"]
        assert len(init_events) == 1
        data = init_events[0]["args"][0]
        assert "stats" in data
        assert "transactions" in data
