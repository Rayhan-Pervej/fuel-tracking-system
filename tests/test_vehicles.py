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
             patch("app.models.vehicle.VehicleModel.get_by_user_id", return_value=vehicles), \
             patch("app.models.vehicle.VehicleModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 1
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
        with patch("app.models.vehicle.VehicleModel.get_all", return_value=vehicles), \
             patch("app.models.vehicle.VehicleModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 1
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
