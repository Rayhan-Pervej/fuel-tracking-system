from unittest.mock import patch


USER = {
    "name": "Rayhan",
    "email": "rayhan@example.com",
    "password": "secret123",
    "role": "customer",
    "license": "DH-1234"
}


class TestCreateUser:
    def test_success(self, client, admin_token):
        created = {
            "_id": "uuid-1",
            "name": "Rayhan",
            "email": "rayhan@example.com",
            "password_hash": "hashed",
            "role": "customer",
            "license": "DH-1234",
            "created_at": "2025-01-01"
        }
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=created):
            res = client.post("/api/users/", json=USER,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        body = res.get_json()
        assert body["status"] == 201
        assert body["data"]["user"]["email"] == "rayhan@example.com"

    def test_no_token(self, client):
        res = client.post("/api/users/", json=USER)
        assert res.status_code == 401

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.post("/api/users/", json=USER,
                          headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_duplicate_email(self, client, admin_token):
        with patch("app.models.user.UserModel.exists_by_email", return_value=True):
            res = client.post("/api/users/", json=USER,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409
        assert res.get_json()["status"] == 409

    def test_missing_name(self, client, admin_token):
        bad = {k: v for k, v in USER.items() if k != "name"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_missing_email(self, client, admin_token):
        bad = {k: v for k, v in USER.items() if k != "email"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "email" in res.get_json()["errors"]

    def test_missing_password(self, client, admin_token):
        bad = {k: v for k, v in USER.items() if k != "password"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "password" in res.get_json()["errors"]

    def test_missing_role_defaults_to_customer(self, client, admin_token):
        bad = {k: v for k, v in USER.items() if k != "role"}
        created = {**bad, "_id": "uuid-1", "role": "customer", "password_hash": "hashed", "created_at": "2025-01-01"}
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=created):
            res = client.post("/api/users/", json=bad,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["user"]["role"] == "customer"

    def test_invalid_role(self, client, admin_token):
        bad = {**USER, "role": "superadmin"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "role" in res.get_json()["errors"]

    def test_invalid_email(self, client, admin_token):
        bad = {**USER, "email": "not-an-email"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "email" in res.get_json()["errors"]

    def test_password_too_short(self, client, admin_token):
        bad = {**USER, "password": "abc"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "password" in res.get_json()["errors"]

    def test_empty_body(self, client, admin_token):
        res = client.post("/api/users/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_no_content_type(self, client, admin_token):
        res = client.post("/api/users/", data="not json",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 415


class TestGetUser:
    def test_get_existing_user(self, client, admin_token):
        user = {**USER, "_id": "uuid-1", "created_at": "2025-01-01"}
        with patch("app.models.user.UserModel.get_by_id", return_value=user):
            res = client.get("/api/users/uuid-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["_id"] == "uuid-1"

    def test_get_nonexistent_user(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.get("/api/users/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404
        assert res.get_json()["status"] == 404

    def test_no_token(self, client):
        res = client.get("/api/users/uuid-1")
        assert res.status_code == 401


class TestGetUsers:
    def test_success(self, client, admin_token):
        users = [{"_id": f"uuid-{i}", "name": f"User{i}", "email": f"u{i}@x.com", "role": "customer"} for i in range(3)]
        with patch("app.services.user_service.UserService.get_filtered", return_value=(users, None, False)):
            res = client.get("/api/users/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        body = res.get_json()
        assert len(body["data"]["users"]) == 3
        assert body["data"]["pagination"]["has_more"] is False
        assert body["data"]["pagination"]["next_cursor"] is None

    def test_no_token(self, client):
        res = client.get("/api/users/")
        assert res.status_code == 401

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.get("/api/users/",
                         headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_invalid_limit_param(self, client, admin_token):
        res = client.get("/api/users/?limit=abc",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_negative_limit(self, client, admin_token):
        res = client.get("/api/users/?limit=-1",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestUpdateUser:
    USER_DB = {"_id": "uuid-1", "name": "Rayhan", "email": "rayhan@example.com",
               "role": "customer", "license": "DH-1234"}

    def test_success(self, client, admin_token):
        updated = {**self.USER_DB, "name": "Updated Name"}
        with patch("app.models.user.UserModel.get_by_id", return_value=self.USER_DB), \
             patch("app.models.user.UserModel.update", return_value=updated):
            res = client.patch("/api/users/uuid-1", json={"name": "Updated Name"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["name"] == "Updated Name"

    def test_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.patch("/api/users/bad-id", json={"name": "Valid Name"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.patch("/api/users/uuid-1", json={"name": "X"})
        assert res.status_code == 401

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.patch("/api/users/uuid-1", json={"name": "X"},
                           headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_empty_body(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=self.USER_DB):
            res = client.patch("/api/users/uuid-1", json={},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_field(self, client, admin_token):
        res = client.patch("/api/users/uuid-1", json={"name": "X"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        # short name validation
        res2 = client.patch("/api/users/uuid-1", json={"name": "X"},
                            headers={"Authorization": f"Bearer {admin_token}"})
        assert res2.status_code == 400
        assert "name" in res2.get_json()["errors"]
