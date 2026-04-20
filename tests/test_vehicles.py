from unittest.mock import patch


VEHICLE = {"vehicle_number": "DH-1234"}
VEHICLE_DB = {"_id": "veh-1", "vehicle_number": "DH-1234", "created_at": "2025-01-01"}


class TestCreateVehicle:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=False), \
             patch("app.models.vehicle.VehicleModel.create", return_value=VEHICLE_DB):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"X-Userinfo": admin_token})
        assert res.status_code == 201
        assert res.get_json()["data"]["vehicle"]["_id"] == "veh-1"

    def test_success_as_employee(self, client, employee_token):
        with patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=False), \
             patch("app.models.vehicle.VehicleModel.create", return_value=VEHICLE_DB):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"X-Userinfo": employee_token})
        assert res.status_code == 201

    def test_no_token(self, client):
        res = client.post("/api/vehicles/", json=VEHICLE)
        assert res.status_code == 401

    def test_duplicate_vehicle_number(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=True):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"X-Userinfo": admin_token})
        assert res.status_code == 409

    def test_missing_vehicle_number(self, client, admin_token):
        res = client.post("/api/vehicles/", json={},
                          headers={"X-Userinfo": admin_token})
        assert res.status_code == 400
        assert "vehicle_number" in res.get_json()["errors"]

    def test_empty_body(self, client, admin_token):
        res = client.post("/api/vehicles/", json={},
                          headers={"X-Userinfo": admin_token})
        assert res.status_code == 400


class TestGetVehicle:
    def test_get_existing(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.get("/api/vehicles/veh-1",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicle"]["_id"] == "veh-1"

    def test_get_as_employee(self, client, employee_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.get("/api/vehicles/veh-1",
                             headers={"X-Userinfo": employee_token})
        assert res.status_code == 200

    def test_get_nonexistent(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.get("/api/vehicles/bad-id",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/vehicles/veh-1")
        assert res.status_code == 401


class TestGetAllVehicles:
    def test_success(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["vehicles"]) == 1

    def test_pagination_structure(self, client, admin_token):
        vehicles = [VEHICLE_DB] * 5
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, "cursor-abc", True)):
            res = client.get("/api/vehicles/?limit=5",
                             headers={"X-Userinfo": admin_token})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"

    def test_filter_by_search(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)) as mock_svc:
            res = client.get("/api/vehicles/?search=DH",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_empty_result(self, client, admin_token):
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/vehicles/",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicles"] == []

    def test_large_dataset(self, client, admin_token):
        vehicles = [{"_id": f"veh-{i}", "vehicle_number": f"DH-{i:04d}"} for i in range(100)]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, "next", True)):
            res = client.get("/api/vehicles/?limit=100",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["vehicles"]) == 100

    def test_no_token(self, client):
        res = client.get("/api/vehicles/")
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.get("/api/vehicles/",
                         headers={"X-Userinfo": employee_token})
        assert res.status_code == 403

    def test_invalid_limit(self, client, admin_token):
        res = client.get("/api/vehicles/?limit=abc",
                         headers={"X-Userinfo": admin_token})
        assert res.status_code == 400

    def test_invalid_negative_limit(self, client, admin_token):
        res = client.get("/api/vehicles/?limit=-5",
                         headers={"X-Userinfo": admin_token})
        assert res.status_code == 400


class TestSearchVehicles:
    def test_success(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/search?q=DH",
                             headers={"X-Userinfo": admin_token})
        assert res.status_code == 200

    def test_success_as_employee(self, client, employee_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/search?q=DH",
                             headers={"X-Userinfo": employee_token})
        assert res.status_code == 200

    def test_missing_q_param(self, client, admin_token):
        res = client.get("/api/vehicles/search",
                         headers={"X-Userinfo": admin_token})
        assert res.status_code == 400

    def test_no_token(self, client):
        res = client.get("/api/vehicles/search?q=DH")
        assert res.status_code == 401


class TestUpdateVehicle:
    def test_success_as_admin(self, client, admin_token):
        updated = {**VEHICLE_DB, "vehicle_number": "DH-9999"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB), \
             patch("app.models.vehicle.VehicleModel.update", return_value=updated):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_number": "DH-9999"},
                               headers={"X-Userinfo": admin_token})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicle"]["vehicle_number"] == "DH-9999"

    def test_forbidden_employee(self, client, employee_token):
        res = client.patch("/api/vehicles/veh-1", json={"vehicle_number": "DH-9999"},
                           headers={"X-Userinfo": employee_token})
        assert res.status_code == 403

    def test_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.patch("/api/vehicles/bad-id", json={"vehicle_number": "DH-9999"},
                               headers={"X-Userinfo": admin_token})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.patch("/api/vehicles/veh-1", json={"vehicle_number": "DH-9999"})
        assert res.status_code == 401

    def test_empty_body(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.patch("/api/vehicles/veh-1", json={},
                               headers={"X-Userinfo": admin_token})
        assert res.status_code == 400


class TestDeleteVehicle:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB), \
             patch("app.models.vehicle.VehicleModel.delete"):
            res = client.delete("/api/vehicles/veh-1",
                                headers={"X-Userinfo": admin_token})
        assert res.status_code == 200

    def test_forbidden_employee(self, client, employee_token):
        res = client.delete("/api/vehicles/veh-1",
                            headers={"X-Userinfo": employee_token})
        assert res.status_code == 403

    def test_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.delete("/api/vehicles/bad-id",
                                headers={"X-Userinfo": admin_token})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.delete("/api/vehicles/veh-1")
        assert res.status_code == 401
