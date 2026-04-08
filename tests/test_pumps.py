from unittest.mock import patch


PUMP = {"_id": "pump-1", "name": "Shell Station", "location": "Dhaka", "license": "P-001"}

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

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.post("/api/pumps/", json=PUMP_PAYLOAD,
                          headers={"Authorization": f"Bearer {employee_token}"})
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
        with patch("app.models.pump.PumpModel.get_all", return_value=pumps), \
             patch("app.models.pump.PumpModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 1
            res = client.get("/api/pumps/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["pumps"]) == 1

    def test_no_token(self, client):
        res = client.get("/api/pumps/")
        assert res.status_code == 401

    def test_invalid_pagination(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_all", return_value=[]), \
             patch("app.models.pump.PumpModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 0
            res = client.get("/api/pumps/?page=abc",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
