from unittest.mock import patch


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
    def test_success(self, client):
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
             patch("app.models.transaction.TransactionModel.create", return_value=created):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD)
        assert res.status_code == 201
        body = res.get_json()
        assert body["status"] == 201
        assert body["data"]["transaction"]["total_price"] == 1250.0

    def test_vehicle_not_found(self, client):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD)
        assert res.status_code == 404
        assert "Vehicle not found" in res.get_json()["message"]

    def test_pump_not_found(self, client):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD)
        assert res.status_code == 404
        assert "Pump not found" in res.get_json()["message"]

    def test_no_active_fuel_price(self, client):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=None):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD)
        assert res.status_code == 404
        assert "No active price" in res.get_json()["message"]

    def test_invalid_fuel_type(self, client):
        bad = {**TRANSACTION_PAYLOAD, "fuel_type": "kerosene"}
        res = client.post("/api/transactions/", json=bad)
        assert res.status_code == 400
        assert "fuel_type" in res.get_json()["errors"]

    def test_quantity_too_low(self, client):
        bad = {**TRANSACTION_PAYLOAD, "quantity": 0.0}
        res = client.post("/api/transactions/", json=bad)
        assert res.status_code == 400
        assert "quantity" in res.get_json()["errors"]

    def test_missing_fields(self, client):
        res = client.post("/api/transactions/", json={})
        assert res.status_code == 400
        errors = res.get_json()["errors"]
        assert "vehicle_id" in errors
        assert "pump_id" in errors
        assert "fuel_type" in errors
        assert "quantity" in errors


class TestGetTransaction:
    def test_get_existing(self, client):
        txn = {**TRANSACTION_PAYLOAD, "_id": "txn-1", "total_price": 1250.0}
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=txn):
            res = client.get("/api/transactions/txn-1")
        assert res.status_code == 200
        assert res.get_json()["data"]["transaction"]["_id"] == "txn-1"

    def test_get_nonexistent(self, client):
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/bad-id")
        assert res.status_code == 404


class TestGetTransactionsByVehicle:
    def test_success(self, client):
        txns = [{"_id": "txn-1", "vehicle_id": "veh-1", "total_price": 1250.0}]
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.transaction.TransactionModel.get_by_vehicle", return_value=txns), \
             patch("app.models.transaction.TransactionModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 1
            res = client.get("/api/transactions/vehicle/veh-1")
        assert res.status_code == 200
        assert res.get_json()["data"]["pagination"]["total"] == 1

    def test_vehicle_not_found(self, client):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/vehicle/bad-id")
        assert res.status_code == 404


class TestGetTransactionsByPump:
    def test_success(self, client):
        txns = [{"_id": "txn-1", "pump_id": "pump-1", "total_price": 1250.0}]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.transaction.TransactionModel.get_by_pump", return_value=txns), \
             patch("app.models.transaction.TransactionModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 1
            res = client.get("/api/transactions/pump/pump-1")
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 1

    def test_pump_not_found(self, client):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/pump/bad-id")
        assert res.status_code == 404
