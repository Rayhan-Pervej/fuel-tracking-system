from unittest.mock import patch, MagicMock


def make_keycloak_response(status_code, json_body):
    res = MagicMock()
    res.status_code = status_code
    res.ok = status_code < 400
    res.json.return_value = json_body
    return res


KEYCLOAK_TOKEN_RESPONSE = {
    "access_token": "eyJhbGciOiJSUzI1NiJ9.test",
    "refresh_token": "refresh-token-value",
    "token_type": "Bearer"
}


class TestLogin:
    def test_success(self, client):
        with patch("app.routes.auth.http.post", return_value=make_keycloak_response(200, KEYCLOAK_TOKEN_RESPONSE)):
            res = client.post("/api/auth/login", json={"email": "rayhan@example.com", "password": "secret123"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_invalid_credentials(self, client):
        with patch("app.routes.auth.http.post", return_value=make_keycloak_response(401, {"error": "invalid_grant"})):
            res = client.post("/api/auth/login", json={"email": "rayhan@example.com", "password": "wrongpass"})
        assert res.status_code == 401

    def test_keycloak_service_error(self, client):
        with patch("app.routes.auth.http.post", return_value=make_keycloak_response(500, {})):
            res = client.post("/api/auth/login", json={"email": "rayhan@example.com", "password": "secret123"})
        assert res.status_code == 502

    def test_missing_email(self, client):
        res = client.post("/api/auth/login", json={"password": "secret123"})
        assert res.status_code == 400

    def test_missing_password(self, client):
        res = client.post("/api/auth/login", json={"email": "rayhan@example.com"})
        assert res.status_code == 400

    def test_empty_body(self, client):
        res = client.post("/api/auth/login", json={})
        assert res.status_code == 400

    def test_no_body(self, client):
        res = client.post("/api/auth/login")
        assert res.status_code in [400, 415]


class TestRefreshToken:
    def test_success(self, client):
        with patch("app.routes.auth.http.post", return_value=make_keycloak_response(200, KEYCLOAK_TOKEN_RESPONSE)):
            res = client.post("/api/auth/refresh", json={"refresh_token": "valid-token"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_missing_refresh_token(self, client):
        res = client.post("/api/auth/refresh", json={})
        assert res.status_code == 400

    def test_invalid_refresh_token(self, client):
        with patch("app.routes.auth.http.post", return_value=make_keycloak_response(400, {"error": "invalid_grant"})):
            res = client.post("/api/auth/refresh", json={"refresh_token": "bad-token"})
        assert res.status_code == 401

    def test_no_body(self, client):
        res = client.post("/api/auth/refresh")
        assert res.status_code in [400, 415]


class TestLogout:
    def test_success(self, client):
        with patch("app.routes.auth.http.post", return_value=make_keycloak_response(204, {})):
            res = client.post("/api/auth/logout", json={"refresh_token": "some-token"})
        assert res.status_code == 200

    def test_missing_refresh_token(self, client):
        res = client.post("/api/auth/logout", json={})
        assert res.status_code == 400
