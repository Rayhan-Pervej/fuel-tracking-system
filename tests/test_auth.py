from unittest.mock import patch


USER = {
    "_id": "user-1",
    "name": "Rayhan",
    "email": "rayhan@example.com",
    "password_hash": "hashed",
    "role": "customer",
    "license": "DH-1234",
    "created_at": "2025-01-01"
}

REGISTER_PAYLOAD = {
    "name": "Rayhan",
    "email": "rayhan@example.com",
    "password": "secret123",
    "license": "DH-1234"
}


class TestLogin:
    def test_success(self, client):
        with patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.user.UserModel.check_password", return_value=True), \
             patch("app.models.user.UserModel.set_refresh_token"):
            res = client.post("/api/auth/login", json={"email": "rayhan@example.com", "password": "secret123"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_response_does_not_include_password_hash(self, client):
        with patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.user.UserModel.check_password", return_value=True), \
             patch("app.models.user.UserModel.set_refresh_token"):
            res = client.post("/api/auth/login", json={"email": "rayhan@example.com", "password": "secret123"})
        assert "password_hash" not in str(res.get_json())

    def test_invalid_password(self, client):
        with patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.user.UserModel.check_password", return_value=False):
            res = client.post("/api/auth/login", json={"email": "rayhan@example.com", "password": "wrongpass"})
        assert res.status_code == 401

    def test_user_not_found(self, client):
        with patch("app.models.user.UserModel.get_by_email", return_value=None):
            res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "secret123"})
        assert res.status_code == 401

    def test_missing_email(self, client):
        res = client.post("/api/auth/login", json={"password": "secret123"})
        assert res.status_code == 400
        assert "email" in res.get_json()["errors"]

    def test_missing_password(self, client):
        res = client.post("/api/auth/login", json={"email": "rayhan@example.com"})
        assert res.status_code == 400
        assert "password" in res.get_json()["errors"]

    def test_invalid_email_format(self, client):
        res = client.post("/api/auth/login", json={"email": "not-an-email", "password": "secret123"})
        assert res.status_code == 400
        assert "email" in res.get_json()["errors"]

    def test_empty_body(self, client):
        res = client.post("/api/auth/login", json={})
        assert res.status_code == 400

    def test_no_body(self, client):
        res = client.post("/api/auth/login")
        assert res.status_code in [400, 415]


class TestRegister:
    def test_success(self, client):
        created = {**USER}
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=created):
            res = client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert res.status_code == 201
        assert "password_hash" not in res.get_json()["data"]["user"]

    def test_role_always_customer(self, client):
        created = {**USER, "role": "customer"}
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=created):
            res = client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert res.status_code == 201
        assert res.get_json()["data"]["user"]["role"] == "customer"

    def test_duplicate_email(self, client):
        with patch("app.models.user.UserModel.exists_by_email", return_value=True):
            res = client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert res.status_code == 409

    def test_cannot_register_as_admin(self, client):
        payload = {**REGISTER_PAYLOAD, "role": "admin"}
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 403

    def test_cannot_register_as_employee(self, client):
        payload = {**REGISTER_PAYLOAD, "role": "employee"}
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 403

    def test_missing_name(self, client):
        bad = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "name"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_missing_email(self, client):
        bad = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "email"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "email" in res.get_json()["errors"]

    def test_missing_password(self, client):
        bad = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "password"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "password" in res.get_json()["errors"]

    def test_missing_license(self, client):
        bad = {k: v for k, v in REGISTER_PAYLOAD.items() if k != "license"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "license" in res.get_json()["errors"]

    def test_invalid_email_format(self, client):
        bad = {**REGISTER_PAYLOAD, "email": "not-an-email"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "email" in res.get_json()["errors"]

    def test_password_too_short(self, client):
        bad = {**REGISTER_PAYLOAD, "password": "abc"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "password" in res.get_json()["errors"]

    def test_name_too_short(self, client):
        bad = {**REGISTER_PAYLOAD, "name": "X"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_license_too_short(self, client):
        bad = {**REGISTER_PAYLOAD, "license": "AB"}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "license" in res.get_json()["errors"]

    def test_license_too_long(self, client):
        bad = {**REGISTER_PAYLOAD, "license": "A" * 11}
        res = client.post("/api/auth/register", json=bad)
        assert res.status_code == 400
        assert "license" in res.get_json()["errors"]

    def test_empty_body(self, client):
        res = client.post("/api/auth/register", json={})
        assert res.status_code == 400


class TestRefreshToken:
    def test_success(self, client):
        user = {**USER}
        with patch("app.models.user.UserModel.get_by_refresh_token", return_value=user):
            res = client.post("/api/auth/refresh", json={"refresh_token": "valid-token"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_missing_refresh_token(self, client):
        res = client.post("/api/auth/refresh", json={})
        assert res.status_code == 400

    def test_invalid_refresh_token(self, client):
        with patch("app.models.user.UserModel.get_by_refresh_token", return_value=None):
            res = client.post("/api/auth/refresh", json={"refresh_token": "bad-token"})
        assert res.status_code == 401

    def test_no_body(self, client):
        res = client.post("/api/auth/refresh")
        assert res.status_code in [400, 415]


class TestLogout:
    def test_success(self, client, admin_token):
        with patch("app.models.user.UserModel.clear_refresh_token"):
            res = client.post("/api/auth/logout",
                              json={"refresh_token": "some-token"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_missing_refresh_token(self, client, admin_token):
        res = client.post("/api/auth/logout", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_no_auth_token(self, client):
        res = client.post("/api/auth/logout", json={"refresh_token": "some-token"})
        assert res.status_code == 401
