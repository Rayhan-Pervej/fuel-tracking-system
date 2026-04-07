from unittest.mock import patch


USER = {"name": "Rayhan", "license": "DH-1234"}


class TestCreateUser:
    def test_success(self, client):
        created = {**USER, "_id": "uuid-1", "created_at": "2025-01-01"}
        with patch("app.models.user.UserModel.exists_by_license", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=created):
            res = client.post("/api/users/", json=USER)
        assert res.status_code == 201
        body = res.get_json()
        assert body["status"] == 201
        assert body["data"]["user"]["license"] == "DH-1234"

    def test_duplicate_license(self, client):
        with patch("app.models.user.UserModel.exists_by_license", return_value=True):
            res = client.post("/api/users/", json=USER)
        assert res.status_code == 409
        assert res.get_json()["status"] == 409

    def test_missing_name(self, client):
        res = client.post("/api/users/", json={"license": "DH-1234"})
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_missing_license(self, client):
        res = client.post("/api/users/", json={"name": "Rayhan"})
        assert res.status_code == 400
        assert "license" in res.get_json()["errors"]

    def test_empty_body(self, client):
        res = client.post("/api/users/", json={})
        assert res.status_code == 400

    def test_no_content_type(self, client):
        # Flask rejects requests without Content-Type: application/json
        res = client.post("/api/users/", data="not json")
        assert res.status_code == 415


class TestGetUser:
    def test_get_existing_user(self, client):
        user = {**USER, "_id": "uuid-1", "created_at": "2025-01-01"}
        with patch("app.models.user.UserModel.get_by_id", return_value=user):
            res = client.get("/api/users/uuid-1")
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["_id"] == "uuid-1"

    def test_get_nonexistent_user(self, client):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.get("/api/users/bad-id")
        assert res.status_code == 404
        assert res.get_json()["status"] == 404


class TestGetUsers:
    def test_pagination_defaults(self, client):
        users = [{"_id": f"uuid-{i}", "name": f"User{i}", "license": f"L{i}"} for i in range(3)]
        with patch("app.models.user.UserModel.get_all", return_value=users), \
             patch("app.models.user.UserModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 3
            res = client.get("/api/users/")
        assert res.status_code == 200
        body = res.get_json()
        assert len(body["data"]["users"]) == 3
        assert body["data"]["pagination"]["total"] == 3
        assert body["data"]["pagination"]["page"] == 1

    def test_invalid_page_param(self, client):
        res = client.get("/api/users/?page=abc")
        assert res.status_code == 400

    def test_invalid_negative_page(self, client):
        res = client.get("/api/users/?page=-1")
        assert res.status_code == 400
