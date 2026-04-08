from unittest.mock import patch, MagicMock


def mock_session():
    """Returns a mock mongo_client that supports start_session() context manager."""
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    txn = MagicMock()
    txn.__enter__ = MagicMock(return_value=txn)
    txn.__exit__ = MagicMock(return_value=False)
    session.start_transaction = MagicMock(return_value=txn)
    client = MagicMock()
    client.start_session = MagicMock(return_value=session)
    return client


VEHICLE = {"_id": "veh-1", "vehicle_number": "DH-1234", "type": "car"}
PUMP = {"_id": "pump-1", "name": "Shell", "location": "Dhaka", "license": "P-001"}
FUEL_PRICE = {"_id": "fp-1", "fuel_type": "octane", "price_per_unit": 125.0, "unit": "liter", "currency": "BDT", "effective_from": "2025-01-01"}

TRANSACTION_PAYLOAD = {
    "vehicle_id": "veh-1",
    "pump_id": "pump-1",
    "fuel_type": "octane",
    "quantity": 10.0
}


class TestCreateTransaction:
    def test_success(self, client, admin_token):
        created = {
            "_id": "txn-1",
            "vehicle_id": "veh-1",
            "pump_id": "pump-1",
            "fuel_price_id": "fp-1",
            "quantity": 10.0,
            "total_price": 1250.0,
            "created_at": "2025-01-01"
        }
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=created), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        body = res.get_json()
        assert body["status"] == 201
        assert body["data"]["transaction"]["total_price"] == 1250.0

    def test_success_as_employee(self, client, employee_token):
        created = {
            "_id": "txn-1",
            "vehicle_id": "veh-1",
            "pump_id": "pump-1",
            "fuel_price_id": "fp-1",
            "quantity": 10.0,
            "total_price": 1250.0,
            "created_at": "2025-01-01"
        }
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=created), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 201

    def test_no_token(self, client):
        res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD)
        assert res.status_code == 401

    def test_forbidden_customer(self, client, customer_token):
        res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                          headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_vehicle_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404
        assert "Vehicle not found" in res.get_json()["message"]

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404
        assert "Pump not found" in res.get_json()["message"]

    def test_no_active_fuel_price(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=None), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404
        assert "No active price" in res.get_json()["message"]

    def test_invalid_fuel_type(self, client, admin_token):
        bad = {**TRANSACTION_PAYLOAD, "fuel_type": "kerosene"}
        res = client.post("/api/transactions/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "fuel_type" in res.get_json()["errors"]

    def test_quantity_too_low(self, client, admin_token):
        bad = {**TRANSACTION_PAYLOAD, "quantity": 0.0}
        res = client.post("/api/transactions/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "quantity" in res.get_json()["errors"]

    def test_missing_fields(self, client, admin_token):
        res = client.post("/api/transactions/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        errors = res.get_json()["errors"]
        assert "vehicle_id" in errors
        assert "pump_id" in errors
        assert "fuel_type" in errors
        assert "quantity" in errors


class TestGetTransaction:
    def test_get_existing(self, client, admin_token):
        txn = {**TRANSACTION_PAYLOAD, "_id": "txn-1", "total_price": 1250.0, "fuel_price_id": "fp-1"}
        vehicle = {"_id": "veh-1", "vehicle_number": "DH-1234"}
        pump = {"_id": "pump-1", "name": "Pump A"}
        fuel_price = {"_id": "fp-1", "fuel_type": "octane", "unit": "liter", "currency": "BDT"}
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=txn), \
             patch("app.models.vehicle.VehicleModel.get_by_id", return_value=vehicle), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=pump), \
             patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=fuel_price):
            res = client.get("/api/transactions/txn-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["transaction"]["_id"] == "txn-1"

    def test_get_nonexistent(self, client, admin_token):
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/transactions/txn-1")
        assert res.status_code == 401


class TestGetTransactionsByVehicle:
    def test_success(self, client, admin_token):
        txns = [{"_id": "txn-1", "vehicle_id": "veh-1", "total_price": 1250.0}]
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/vehicle/veh-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["pagination"]["has_more"] is False

    def test_vehicle_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/vehicle/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/transactions/vehicle/veh-1")
        assert res.status_code == 401


class TestGetTransactionsByPump:
    def test_success(self, client, admin_token):
        txns = [{"_id": "txn-1", "pump_id": "pump-1", "total_price": 1250.0}]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/pump/pump-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 1

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/pump/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/transactions/pump/pump-1")
        assert res.status_code == 401


class TestGetAllTransactions:
    def test_success(self, client, admin_token):
        txns = [{"_id": "txn-1", "vehicle_id": "veh-1", "total_price": 1250.0}]
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_no_token(self, client):
        res = client.get("/api/transactions/")
        assert res.status_code == 401

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.get("/api/transactions/",
                         headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403
