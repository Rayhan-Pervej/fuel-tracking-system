from unittest.mock import patch


VEHICLE = {"user_id": "user-1", "vehicle_number": "DH-1234", "vehicle_type": "car"}
USER = {"_id": "user-1", "name": "Rayhan", "license": "DH-001"}


class TestCreateVehicle:
    def test_success(self, client, admin_token):
        created = {**VEHICLE, "_id": "veh-1", "type": "car", "created_at": "2025-01-01"}
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=False), \
             patch("app.models.vehicle.VehicleModel.create", return_value=created):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["status"] == 201
        assert res.get_json()["data"]["vehicle"]["_id"] == "veh-1"

    def test_no_token(self, client):
        res = client.post("/api/vehicles/", json=VEHICLE)
        assert res.status_code == 401

    def test_user_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404
        assert "User not found" in res.get_json()["message"]

    def test_duplicate_vehicle_number(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=True):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_invalid_vehicle_type(self, client, admin_token):
        bad = {**VEHICLE, "vehicle_type": "spaceship"}
        with patch("app.models.user.UserModel.get_by_id", return_value=USER):
            res = client.post("/api/vehicles/", json=bad,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "vehicle_type" in res.get_json()["errors"]

    def test_missing_user_id(self, client, admin_token):
        res = client.post("/api/vehicles/",
                          json={"vehicle_number": "DH-1234", "vehicle_type": "car"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "user_id" in res.get_json()["errors"]


class TestGetVehicle:
    def test_get_existing(self, client, admin_token):
        vehicle = {**VEHICLE, "_id": "veh-1", "type": "car"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=vehicle):
            res = client.get("/api/vehicles/veh-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicle"]["_id"] == "veh-1"

    def test_get_nonexistent(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.get("/api/vehicles/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/vehicles/veh-1")
        assert res.status_code == 401


class TestGetVehiclesByUser:
    def test_success(self, client, admin_token):
        vehicles = [{"_id": "veh-1", "user_id": "user-1", "vehicle_number": "DH-1234", "type": "car"}]
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/user/user-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["vehicles"]) == 1

    def test_user_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.get("/api/vehicles/user/bad-user",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/vehicles/user/user-1")
        assert res.status_code == 401


class TestGetAllVehicles:
    def test_success(self, client, admin_token):
        vehicles = [{"_id": "veh-1", "user_id": "user-1", "vehicle_number": "DH-1234", "type": "car"}]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_no_token(self, client):
        res = client.get("/api/vehicles/")
        assert res.status_code == 401

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.get("/api/vehicles/",
                         headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403


class TestUpdateVehicle:
    VEHICLE_DB = {"_id": "veh-1", "user_id": "user-1", "vehicle_number": "DH-1234", "type": "car"}

    def test_success_as_admin(self, client, admin_token):
        updated = {**self.VEHICLE_DB, "type": "truck"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=self.VEHICLE_DB), \
             patch("app.models.vehicle.VehicleModel.update", return_value=updated):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicle"]["type"] == "truck"

    def test_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.patch("/api/vehicles/bad-id", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"})
        assert res.status_code == 401

    def test_forbidden_other_user(self, client, customer_token):
        other_vehicle = {**self.VEHICLE_DB, "user_id": "other-user"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=other_vehicle):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_empty_body(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=self.VEHICLE_DB):
            res = client.patch("/api/vehicles/veh-1", json={},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_vehicle_type(self, client, admin_token):
        res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "spaceship"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "vehicle_type" in res.get_json()["errors"]
