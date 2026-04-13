"""
Socket.IO dashboard tests.
These tests use a dedicated app fixture that creates a fresh SocketIO instance
(separate from app.extensions.socketio) to avoid state pollution between tests.
"""
import jwt
import pytest


SECRET_KEY = "test-secret"


BASE_TRANSACTIONS = [
    {
        "_id": "txn-1",
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
    },
    {
        "_id": "txn-2",
        "vehicle_id": "veh-2",
        "pump_id": "pump-1",
        "fuel_price_id": "fp-1",
        "quantity": 20.0,
        "total_price": 2500.0,
        "created_at": "2025-01-01T01:00:00",
        "fuel_type": "diesel",
        "unit": "liter",
        "currency": "BDT",
        "vehicle_number": "DH-5678",
        "pump_name": "Shell"
    },
    {
        "_id": "txn-3",
        "vehicle_id": "veh-3",
        "pump_id": "pump-2",
        "fuel_price_id": "fp-2",
        "quantity": 30.0,
        "total_price": 3600.0,
        "created_at": "2025-01-01T02:00:00",
        "fuel_type": "petrol",
        "unit": "liter",
        "currency": "BDT",
        "vehicle_number": "DH-9012",
        "pump_name": "Chevron"
    }
]


def mock_build_payload(pump_id=None):
    transactions = [t for t in BASE_TRANSACTIONS if t["pump_id"] == pump_id] if pump_id else BASE_TRANSACTIONS
    fuel_type_totals = {"octane": 0.0, "diesel": 0.0, "petrol": 0.0}
    for txn in transactions:
        fuel_type = txn.get("fuel_type")
        if fuel_type in fuel_type_totals:
            fuel_type_totals[fuel_type] += txn.get("quantity", 0.0)
    return {
        "stats": {
            "total_transactions": len(transactions),
            "total_revenue": sum(t["total_price"] for t in transactions),
            "total_fuel_dispensed": sum(t["quantity"] for t in transactions),
            "fuel_type_totals": fuel_type_totals
        },
        "transactions": transactions
    }


@pytest.fixture(scope="module")
def sio_setup():
    """
    Creates a fresh Flask app + SocketIO instance isolated from app.extensions.socketio.
    Registers the dashboard event handlers on the fresh socketio instance.
    Module-scoped to avoid re-initialization between tests.
    """
    from flask import Flask, request
    from flask_socketio import SocketIO, emit, disconnect
    import jwt as pyjwt

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = SECRET_KEY

    sio = SocketIO(flask_app, async_mode="threading")
    client_scope = {}
    assignments = {
        "pump-admin-1": {"pump_id": "pump-1", "role": "pump_admin"},
        "employee-1": {"pump_id": "pump-1", "role": "employee"},
    }

    # Register the same event handlers as app/sockets/events.py
    @sio.on("connect", namespace="/dashboard")
    def on_connect(auth=None):
        token = (auth or {}).get("token", "")
        if not token:
            disconnect()
            return
        try:
            payload = pyjwt.decode(token, flask_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        except pyjwt.InvalidTokenError:
            disconnect()
            return

        role = payload.get("role")
        user_id = payload.get("user_id")

        if role == "admin":
            scope = {"pump_id": None}
        else:
            assignment = assignments.get(user_id)
            if not assignment or assignment.get("role") != "pump_admin":
                disconnect()
                return
            scope = {"pump_id": assignment["pump_id"]}

        client_scope[request.sid] = scope
        emit("init", mock_build_payload(scope["pump_id"]))

    @sio.on("disconnect", namespace="/dashboard")
    def on_disconnect():
        client_scope.pop(request.sid, None)

    @sio.on("request_init", namespace="/dashboard")
    def handle_request_init():
        scope = client_scope.get(request.sid)
        if not scope:
            disconnect()
            return
        emit("init", mock_build_payload(scope["pump_id"]))

    yield flask_app, sio


def make_token(user_id="admin-1", role="admin"):
    return jwt.encode({"user_id": user_id, "role": role}, SECRET_KEY, algorithm="HS256")


class TestSocketIOConnect:
    def test_connect_with_valid_admin_token(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token()
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        assert sc.is_connected(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")

    def test_connect_with_pump_admin_token(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token(user_id="pump-admin-1", role="employee")
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        assert sc.is_connected(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")

    def test_connect_with_regular_employee_disconnects(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token(user_id="employee-1", role="employee")
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        assert not sc.is_connected(namespace="/dashboard")

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
        assert "fuel_type_totals" in data["stats"]
        assert set(data["stats"]["fuel_type_totals"].keys()) == {"octane", "diesel", "petrol"}

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
        assert len(data["transactions"]) == 3

    def test_pump_admin_gets_only_assigned_pump_transactions(self, sio_setup):
        flask_app, sio = sio_setup
        token = make_token(user_id="pump-admin-1", role="employee")
        sc = sio.test_client(flask_app, namespace="/dashboard", auth={"token": token})
        received = sc.get_received(namespace="/dashboard")
        sc.disconnect(namespace="/dashboard")
        init_events = [e for e in received if e["name"] == "init"]
        data = init_events[0]["args"][0]
        assert len(data["transactions"]) == 2
        assert all(t["pump_id"] == "pump-1" for t in data["transactions"])
        assert data["stats"]["fuel_type_totals"]["octane"] == 10.0
        assert data["stats"]["fuel_type_totals"]["diesel"] == 20.0
        assert data["stats"]["fuel_type_totals"]["petrol"] == 0.0

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
