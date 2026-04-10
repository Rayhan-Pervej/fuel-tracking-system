from unittest.mock import patch, MagicMock


def mock_session():
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


VEHICLE = {"_id": "veh-1", "vehicle_number": "DH-1234"}
PUMP = {"_id": "pump-1", "name": "Shell", "location": "Dhaka", "license": "P-001"}
FUEL_PRICE = {
    "_id": "fp-1",
    "fuel_type": "octane",
    "price_per_unit": 125.0,
    "unit": "liter",
    "currency": "BDT",
    "effective_from": "2025-01-01"
}
TRANSACTION = {
    "_id": "txn-1",
    "vehicle_id": "veh-1",
    "pump_id": "pump-1",
    "fuel_price_id": "fp-1",
    "quantity": 10.0,
    "total_price": 1250.0,
    "created_at": "2025-01-01T00:00:00"
}
TRANSACTION_PAYLOAD = {
    "vehicle_number": "DH-1234",
    "pump_id": "pump-1",
    "fuel_type": "octane",
    "quantity": 10.0
}


class TestCreateTransaction:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=TRANSACTION), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["transaction"]["total_price"] == 1250.0

    def test_vehicle_auto_created_if_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=None), \
             patch("app.models.vehicle.VehicleModel.create", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=TRANSACTION), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201

    def test_success_as_employee_assigned_to_pump(self, client, employee_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=TRANSACTION), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 201

    def test_forbidden_employee_not_assigned_to_pump(self, client, employee_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD)
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404
        assert "Pump not found" in res.get_json()["message"]

    def test_no_active_fuel_price(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
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

    def test_missing_all_required_fields(self, client, admin_token):
        res = client.post("/api/transactions/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        errors = res.get_json()["errors"]
        assert "vehicle_number" in errors
        assert "pump_id" in errors
        assert "fuel_type" in errors
        assert "quantity" in errors

    def test_all_fuel_types_valid(self, client, admin_token):
        for ftype in ["octane", "diesel", "petrol"]:
            payload = {**TRANSACTION_PAYLOAD, "fuel_type": ftype}
            with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
                 patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
                 patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value={**FUEL_PRICE, "fuel_type": ftype}), \
                 patch("app.models.transaction.TransactionModel.create", return_value=TRANSACTION), \
                 patch("app.routes.transaction.mongo_client", mock_session()):
                res = client.post("/api/transactions/", json=payload,
                                  headers={"Authorization": f"Bearer {admin_token}"})
            assert res.status_code == 201, f"fuel_type '{ftype}' should be valid"

    def test_total_price_matches_succeeds(self, client, admin_token):
        payload = {**TRANSACTION_PAYLOAD, "total_price": 1250.0}
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=TRANSACTION), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=payload,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201

    def test_total_price_mismatch_rejected(self, client, admin_token):
        payload = {**TRANSACTION_PAYLOAD, "total_price": 999.0}
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=payload,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "mismatch" in res.get_json()["message"].lower()

    def test_total_price_omitted_still_succeeds(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.find_by_number", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE), \
             patch("app.models.transaction.TransactionModel.create", return_value=TRANSACTION), \
             patch("app.routes.transaction.mongo_client", mock_session()):
            res = client.post("/api/transactions/", json=TRANSACTION_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201

    def test_total_price_too_low_rejected(self, client, admin_token):
        payload = {**TRANSACTION_PAYLOAD, "total_price": 0.0}
        res = client.post("/api/transactions/", json=payload,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "total_price" in res.get_json()["errors"]


class TestGetTransaction:
    def test_success_as_admin(self, client, admin_token):
        txn = {**TRANSACTION}
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=txn), \
             patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=FUEL_PRICE):
            res = client.get("/api/transactions/txn-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["transaction"]["_id"] == "txn-1"

    def test_enrichment_fields_present(self, client, admin_token):
        txn = {**TRANSACTION}
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=txn), \
             patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=FUEL_PRICE):
            res = client.get("/api/transactions/txn-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        data = res.get_json()["data"]["transaction"]
        assert "vehicle_number" in data
        assert "pump_name" in data
        assert "fuel_type" in data
        assert "unit" in data
        assert "currency" in data

    def test_success_as_pump_employee(self, client, employee_token):
        txn = {**TRANSACTION}
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=txn), \
             patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=FUEL_PRICE):
            res = client.get("/api/transactions/txn-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_forbidden_unrelated_employee(self, client, employee_token):
        txn = {**TRANSACTION}
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=txn), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.get("/api/transactions/txn-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_not_found(self, client, admin_token):
        with patch("app.models.transaction.TransactionModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/transactions/txn-1")
        assert res.status_code == 401


class TestGetAllTransactions:
    def test_success(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 1

    def test_filter_by_vehicle_number(self, client, admin_token):
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=([TRANSACTION], None, False)) as mock_svc:
            res = client.get("/api/transactions/?vehicle_number=DH-1234",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_pump_name(self, client, admin_token):
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=([TRANSACTION], None, False)) as mock_svc:
            res = client.get("/api/transactions/?pump_name=Shell",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_pump_license(self, client, admin_token):
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=([TRANSACTION], None, False)) as mock_svc:
            res = client.get("/api/transactions/?pump_license=P-001",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_fuel_type(self, client, admin_token):
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=([TRANSACTION], None, False)) as mock_svc:
            res = client.get("/api/transactions/?fuel_type=octane",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_date_range(self, client, admin_token):
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=([TRANSACTION], None, False)) as mock_svc:
            res = client.get("/api/transactions/?from=2025-01-01&to=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_date_from_without_to_rejected(self, client, admin_token):
        res = client.get("/api/transactions/?from=2025-01-01",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_date_to_without_from_rejected(self, client, admin_token):
        res = client.get("/api/transactions/?to=2025-12-31",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_date_format(self, client, admin_token):
        res = client.get("/api/transactions/?from=01-01-2025&to=12-31-2025",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_pagination_structure(self, client, admin_token):
        txns = [TRANSACTION] * 5
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, "cursor-abc", True)):
            res = client.get("/api/transactions/?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"

    def test_large_dataset(self, client, admin_token):
        txns = [{"_id": f"txn-{i}", **TRANSACTION} for i in range(100)]
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, "next", True)):
            res = client.get("/api/transactions/?limit=100",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 100

    def test_empty_result(self, client, admin_token):
        with patch("app.services.transaction_service.TransactionService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/transactions/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["transactions"] == []

    def test_no_token(self, client):
        res = client.get("/api/transactions/")
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.get("/api/transactions/",
                         headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_invalid_limit(self, client, admin_token):
        res = client.get("/api/transactions/?limit=abc",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestGetTransactionsByVehicle:
    def test_success_as_admin(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/vehicle/veh-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 1

    def test_success_as_employee(self, client, employee_token):
        txns = [TRANSACTION]
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/vehicle/veh-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_filter_by_fuel_type(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)) as mock_svc:
            res = client.get("/api/transactions/vehicle/veh-1?fuel_type=octane",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_date_range(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)) as mock_svc:
            res = client.get("/api/transactions/vehicle/veh-1?from=2025-01-01&to=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_date_from_without_to_rejected(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE):
            res = client.get("/api/transactions/vehicle/veh-1?from=2025-01-01",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_date_to_without_from_rejected(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE):
            res = client.get("/api/transactions/vehicle/veh-1?to=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_date_format(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE):
            res = client.get("/api/transactions/vehicle/veh-1?from=01-01-2025&to=12-31-2025",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_vehicle_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/vehicle/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/transactions/vehicle/veh-1")
        assert res.status_code == 401

    def test_invalid_limit(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE):
            res = client.get("/api/transactions/vehicle/veh-1?limit=abc",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_pagination_structure(self, client, admin_token):
        txns = [TRANSACTION] * 5
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, "cursor-abc", True)):
            res = client.get("/api/transactions/vehicle/veh-1?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True


class TestGetTransactionsByPump:
    def test_success_as_admin(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/pump/pump-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 1

    def test_success_as_assigned_employee(self, client, employee_token):
        txns = [TRANSACTION]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/pump/pump-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_success_as_pump_admin(self, client, pump_admin_token):
        txns = [TRANSACTION]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)):
            res = client.get("/api/transactions/pump/pump-1",
                             headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 200

    def test_forbidden_unassigned_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.get("/api/transactions/pump/pump-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_filter_by_fuel_type(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)) as mock_svc:
            res = client.get("/api/transactions/pump/pump-1?fuel_type=octane",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_date_range(self, client, admin_token):
        txns = [TRANSACTION]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, None, False)) as mock_svc:
            res = client.get("/api/transactions/pump/pump-1?from=2025-01-01&to=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_date_from_without_to_rejected(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/transactions/pump/pump-1?from=2025-01-01",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_date_to_without_from_rejected(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/transactions/pump/pump-1?to=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_date_format(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/transactions/pump/pump-1?from=01-01-2025&to=12-31-2025",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.get("/api/transactions/pump/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/transactions/pump/pump-1")
        assert res.status_code == 401

    def test_invalid_limit(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/transactions/pump/pump-1?limit=abc",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_large_dataset(self, client, admin_token):
        txns = [{"_id": f"txn-{i}", **TRANSACTION} for i in range(100)]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, "next", True)):
            res = client.get("/api/transactions/pump/pump-1?limit=100",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["transactions"]) == 100

    def test_pagination_structure(self, client, admin_token):
        txns = [TRANSACTION] * 5
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.services.transaction_service.TransactionService.get_filtered", return_value=(txns, "cursor-abc", True)):
            res = client.get("/api/transactions/pump/pump-1?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"
