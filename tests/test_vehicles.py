from unittest.mock import patch


VEHICLE = {"user_id": "user-1", "vehicle_number": "DH-1234", "vehicle_type": "car"}
VEHICLE_DB = {"_id": "veh-1", "user_id": "user-1", "vehicle_number": "DH-1234", "vehicle_type": "car", "created_at": "2025-01-01"}
USER = {"_id": "user-1", "name": "Rayhan", "license": "DH-001"}


class TestCreateVehicle:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=False), \
             patch("app.models.vehicle.VehicleModel.create", return_value=VEHICLE_DB):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["vehicle"]["_id"] == "veh-1"

    def test_success_as_owner(self, client, customer_token):
        # customer_token has user_id "user-3", creating vehicle for themselves
        vehicle_for_owner = {**VEHICLE, "user_id": "user-3"}
        created = {**VEHICLE_DB, "user_id": "user-3"}
        with patch("app.models.user.UserModel.get_by_id", return_value={**USER, "_id": "user-3"}), \
             patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=False), \
             patch("app.models.vehicle.VehicleModel.create", return_value=created):
            res = client.post("/api/vehicles/", json=vehicle_for_owner,
                              headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 201

    def test_forbidden_create_for_other_user(self, client, customer_token):
        # customer_token user_id is "user-3", trying to create for "user-1"
        with patch("app.models.user.UserModel.get_by_id", return_value=USER):
            res = client.post("/api/vehicles/", json=VEHICLE,
                              headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

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

    def test_missing_vehicle_number(self, client, admin_token):
        res = client.post("/api/vehicles/",
                          json={"user_id": "user-1", "vehicle_type": "car"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "vehicle_number" in res.get_json()["errors"]

    def test_missing_vehicle_type(self, client, admin_token):
        res = client.post("/api/vehicles/",
                          json={"user_id": "user-1", "vehicle_number": "DH-1234"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "vehicle_type" in res.get_json()["errors"]

    def test_empty_body(self, client, admin_token):
        res = client.post("/api/vehicles/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_all_vehicle_types_valid(self, client, admin_token):
        for vtype in ["car", "truck", "bike", "bus"]:
            payload = {**VEHICLE, "vehicle_type": vtype}
            created = {**VEHICLE_DB, "vehicle_type": vtype}
            with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
                 patch("app.models.vehicle.VehicleModel.exists_by_number", return_value=False), \
                 patch("app.models.vehicle.VehicleModel.create", return_value=created):
                res = client.post("/api/vehicles/", json=payload,
                                  headers={"Authorization": f"Bearer {admin_token}"})
            assert res.status_code == 201, f"vehicle_type '{vtype}' should be valid"


class TestGetVehicle:
    def test_get_existing(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.get("/api/vehicles/veh-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicle"]["_id"] == "veh-1"

    def test_get_as_owner(self, client, customer_token):
        # customer_token user_id is "user-3"
        own_vehicle = {**VEHICLE_DB, "user_id": "user-3"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=own_vehicle):
            res = client.get("/api/vehicles/veh-1",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_forbidden_other_user_vehicle(self, client, customer_token):
        # customer_token user_id is "user-3", vehicle belongs to "user-1"
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.get("/api/vehicles/veh-1",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_get_nonexistent(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.get("/api/vehicles/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/vehicles/veh-1")
        assert res.status_code == 401


class TestGetAllVehicles:
    def test_success(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["vehicles"]) == 1

    def test_pagination_structure(self, client, admin_token):
        vehicles = [VEHICLE_DB] * 5
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, "cursor-abc", True)):
            res = client.get("/api/vehicles/?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"

    def test_filter_by_type(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)) as mock_svc:
            res = client.get("/api/vehicles/?type=car",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_user_email(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)) as mock_svc:
            res = client.get("/api/vehicles/?user_email=rayhan@example.com",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_search(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)) as mock_svc:
            res = client.get("/api/vehicles/?search=DH",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_empty_result(self, client, admin_token):
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/vehicles/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicles"] == []

    def test_large_dataset(self, client, admin_token):
        vehicles = [{"_id": f"veh-{i}", "user_id": "user-1", "vehicle_number": f"DH-{i:04d}", "vehicle_type": "car"} for i in range(100)]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, "next", True)):
            res = client.get("/api/vehicles/?limit=100",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["vehicles"]) == 100

    def test_no_token(self, client):
        res = client.get("/api/vehicles/")
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.get("/api/vehicles/",
                         headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_forbidden_customer(self, client, customer_token):
        res = client.get("/api/vehicles/",
                         headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_invalid_limit(self, client, admin_token):
        res = client.get("/api/vehicles/?limit=abc",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_negative_limit(self, client, admin_token):
        res = client.get("/api/vehicles/?limit=-5",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestSearchVehicles:
    def test_success(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/search?q=DH",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_success_as_employee(self, client, employee_token):
        vehicles = [VEHICLE_DB]
        with patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/search?q=DH",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_missing_q_param(self, client, admin_token):
        res = client.get("/api/vehicles/search",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_forbidden_customer(self, client, customer_token):
        res = client.get("/api/vehicles/search?q=DH",
                         headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.get("/api/vehicles/search?q=DH")
        assert res.status_code == 401


class TestGetVehiclesByUser:
    def test_success_as_admin(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/user/user-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["vehicles"]) == 1

    def test_success_as_owner(self, client, customer_token):
        # customer_token user_id is "user-3"
        own_user = {**USER, "_id": "user-3"}
        vehicles = [{**VEHICLE_DB, "user_id": "user-3"}]
        with patch("app.models.user.UserModel.get_by_id", return_value=own_user), \
             patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)):
            res = client.get("/api/vehicles/user/user-3",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_forbidden_other_user(self, client, customer_token):
        # customer_token user_id is "user-3", accessing "user-1"
        with patch("app.models.user.UserModel.get_by_id", return_value=USER):
            res = client.get("/api/vehicles/user/user-1",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_user_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.get("/api/vehicles/user/bad-user",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_filter_by_search(self, client, admin_token):
        vehicles = [VEHICLE_DB]
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=(vehicles, None, False)) as mock_svc:
            res = client.get("/api/vehicles/user/user-1?search=DH",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_empty_result(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.services.vehicle_service.VehicleService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/vehicles/user/user-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicles"] == []

    def test_no_token(self, client):
        res = client.get("/api/vehicles/user/user-1")
        assert res.status_code == 401

    def test_invalid_limit(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER):
            res = client.get("/api/vehicles/user/user-1?limit=abc",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestUpdateVehicle:
    def test_success_as_admin(self, client, admin_token):
        updated = {**VEHICLE_DB, "vehicle_type": "truck"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB), \
             patch("app.models.vehicle.VehicleModel.update", return_value=updated):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["vehicle"]["vehicle_type"] == "truck"

    def test_success_as_owner(self, client, customer_token):
        # customer_token user_id is "user-3"
        own_vehicle = {**VEHICLE_DB, "user_id": "user-3"}
        updated = {**own_vehicle, "vehicle_type": "truck"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=own_vehicle), \
             patch("app.models.vehicle.VehicleModel.update", return_value=updated):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_forbidden_other_user(self, client, customer_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.patch("/api/vehicles/bad-id", json={"vehicle_type": "truck"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "truck"})
        assert res.status_code == 401

    def test_empty_body(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.patch("/api/vehicles/veh-1", json={},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_vehicle_type(self, client, admin_token):
        res = client.patch("/api/vehicles/veh-1", json={"vehicle_type": "spaceship"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "vehicle_type" in res.get_json()["errors"]

    def test_update_vehicle_number(self, client, admin_token):
        updated = {**VEHICLE_DB, "vehicle_number": "DH-9999"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB), \
             patch("app.models.vehicle.VehicleModel.update", return_value=updated):
            res = client.patch("/api/vehicles/veh-1", json={"vehicle_number": "DH-9999"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200


class TestDeleteVehicle:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB), \
             patch("app.models.vehicle.VehicleModel.delete"):
            res = client.delete("/api/vehicles/veh-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_success_as_owner(self, client, customer_token):
        own_vehicle = {**VEHICLE_DB, "user_id": "user-3"}
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=own_vehicle), \
             patch("app.models.vehicle.VehicleModel.delete"):
            res = client.delete("/api/vehicles/veh-1",
                                headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_forbidden_other_user(self, client, customer_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=VEHICLE_DB):
            res = client.delete("/api/vehicles/veh-1",
                                headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_not_found(self, client, admin_token):
        with patch("app.models.vehicle.VehicleModel.get_by_id", return_value=None):
            res = client.delete("/api/vehicles/bad-id",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.delete("/api/vehicles/veh-1")
        assert res.status_code == 401
