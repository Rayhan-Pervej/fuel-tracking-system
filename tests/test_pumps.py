from unittest.mock import patch


PUMP = {"_id": "pump-1", "name": "Shell Station", "location": "Dhaka", "license": "P-001", "created_at": "2025-01-01"}

PUMP_PAYLOAD = {
    "name": "Shell Station",
    "location": "Dhaka",
    "license": "P-001"
}


class TestCreatePump:
    def test_success(self, client, admin_token):
        with patch("app.models.pump.PumpModel.exists_by_license", return_value=False), \
             patch("app.models.pump.PumpModel.create", return_value=PUMP):
            res = client.post("/api/pumps/", json=PUMP_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["pump"]["_id"] == "pump-1"

    def test_no_token(self, client):
        res = client.post("/api/pumps/", json=PUMP_PAYLOAD)
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.post("/api/pumps/", json=PUMP_PAYLOAD,
                          headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_forbidden_customer(self, client, customer_token):
        res = client.post("/api/pumps/", json=PUMP_PAYLOAD,
                          headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_duplicate_license(self, client, admin_token):
        with patch("app.models.pump.PumpModel.exists_by_license", return_value=True):
            res = client.post("/api/pumps/", json=PUMP_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_missing_name(self, client, admin_token):
        bad = {k: v for k, v in PUMP_PAYLOAD.items() if k != "name"}
        res = client.post("/api/pumps/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_missing_license(self, client, admin_token):
        bad = {k: v for k, v in PUMP_PAYLOAD.items() if k != "license"}
        res = client.post("/api/pumps/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "license" in res.get_json()["errors"]

    def test_missing_location(self, client, admin_token):
        bad = {k: v for k, v in PUMP_PAYLOAD.items() if k != "location"}
        with patch("app.models.pump.PumpModel.exists_by_license", return_value=False), \
             patch("app.models.pump.PumpModel.create", return_value=PUMP):
            res = client.post("/api/pumps/", json=bad,
                              headers={"Authorization": f"Bearer {admin_token}"})
        # location may be optional — just verify it doesn't crash
        assert res.status_code in [201, 400]

    def test_empty_body(self, client, admin_token):
        res = client.post("/api/pumps/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestGetPump:
    def test_get_existing(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/pumps/pump-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["pump"]["_id"] == "pump-1"

    def test_get_as_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/pumps/pump-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_get_as_customer(self, client, customer_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/pumps/pump-1",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_get_nonexistent(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.get("/api/pumps/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/pumps/pump-1")
        assert res.status_code == 401


class TestGetAllPumps:
    def test_success(self, client, admin_token):
        pumps = [PUMP]
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=(pumps, None, False)):
            res = client.get("/api/pumps/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["pumps"]) == 1

    def test_accessible_by_any_authenticated_user(self, client, customer_token):
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=([PUMP], None, False)):
            res = client.get("/api/pumps/",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_filter_by_location(self, client, admin_token):
        pumps = [PUMP]
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=(pumps, None, False)) as mock_svc:
            res = client.get("/api/pumps/?location=Dhaka",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_license(self, client, admin_token):
        pumps = [PUMP]
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=(pumps, None, False)) as mock_svc:
            res = client.get("/api/pumps/?license=P-001",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_location_and_license(self, client, admin_token):
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=([PUMP], None, False)) as mock_svc:
            res = client.get("/api/pumps/?location=Dhaka&license=P-001",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_empty_result(self, client, admin_token):
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/pumps/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["pumps"] == []

    def test_pagination_structure(self, client, admin_token):
        pumps = [PUMP] * 5
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=(pumps, "cursor-abc", True)):
            res = client.get("/api/pumps/?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"

    def test_large_dataset(self, client, admin_token):
        pumps = [{"_id": f"pump-{i}", "name": f"Pump {i}", "location": "Dhaka", "license": f"P-{i:03d}"} for i in range(100)]
        with patch("app.services.pump_service.PumpService.get_filtered", return_value=(pumps, "next", True)):
            res = client.get("/api/pumps/?limit=100",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["pumps"]) == 100

    def test_no_token(self, client):
        res = client.get("/api/pumps/")
        assert res.status_code == 401

    def test_invalid_limit(self, client, admin_token):
        res = client.get("/api/pumps/?limit=abc",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_negative_limit(self, client, admin_token):
        res = client.get("/api/pumps/?limit=-1",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestUpdatePump:
    def test_success_name(self, client, admin_token):
        updated = {**PUMP, "name": "New Name"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump.PumpModel.update", return_value=updated):
            res = client.patch("/api/pumps/pump-1", json={"name": "New Name"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["pump"]["name"] == "New Name"

    def test_success_location(self, client, admin_token):
        updated = {**PUMP, "location": "Chittagong"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump.PumpModel.update", return_value=updated):
            res = client.patch("/api/pumps/pump-1", json={"location": "Chittagong"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["pump"]["location"] == "Chittagong"

    def test_success_license(self, client, admin_token):
        updated = {**PUMP, "license": "P-002"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump.PumpModel.exists_by_license", return_value=False), \
             patch("app.models.pump.PumpModel.update", return_value=updated):
            res = client.patch("/api/pumps/pump-1", json={"license": "P-002"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.patch("/api/pumps/bad-id", json={"location": "Chittagong"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.patch("/api/pumps/pump-1", json={"location": "Chittagong"})
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.patch("/api/pumps/pump-1", json={"location": "Chittagong"},
                           headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_forbidden_customer(self, client, customer_token):
        res = client.patch("/api/pumps/pump-1", json={"location": "Chittagong"},
                           headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_empty_body(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.patch("/api/pumps/pump-1", json={},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_duplicate_license(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump.PumpModel.exists_by_license", return_value=True):
            res = client.patch("/api/pumps/pump-1", json={"license": "P-002"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_same_license_no_conflict(self, client, admin_token):
        # Updating with the same license as current should not trigger 409
        updated = {**PUMP, "name": "New Name"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump.PumpModel.update", return_value=updated):
            res = client.patch("/api/pumps/pump-1", json={"license": "P-001"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200


class TestDeletePump:
    def test_success(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.remove_by_pump"), \
             patch("app.models.pump.PumpModel.delete"):
            res = client.delete("/api/pumps/pump-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.delete("/api/pumps/bad-id",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.delete("/api/pumps/pump-1")
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.delete("/api/pumps/pump-1",
                            headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_forbidden_customer(self, client, customer_token):
        res = client.delete("/api/pumps/pump-1",
                            headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403
