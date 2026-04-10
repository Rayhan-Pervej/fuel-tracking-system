from unittest.mock import patch


USER = {
    "name": "Rayhan",
    "email": "rayhan@example.com",
    "password": "secret123",
    "role": "employee",
}

USER_DB = {
    "_id": "uuid-1",
    "name": "Rayhan",
    "email": "rayhan@example.com",
    "password_hash": "hashed",
    "role": "employee",
    "created_at": "2025-01-01"
}


class TestCreateUser:
    def test_success(self, client, admin_token):
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=USER_DB):
            res = client.post("/api/users/", json=USER,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        body = res.get_json()
        assert body["status"] == 201
        assert body["data"]["user"]["email"] == "rayhan@example.com"

    def test_password_hash_not_returned(self, client, admin_token):
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=USER_DB):
            res = client.post("/api/users/", json=USER,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert "password_hash" not in res.get_json()["data"]["user"]

    def test_no_token(self, client):
        res = client.post("/api/users/", json=USER)
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.post("/api/users/", json=USER,
                          headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_duplicate_email(self, client, admin_token):
        with patch("app.models.user.UserModel.exists_by_email", return_value=True):
            res = client.post("/api/users/", json=USER,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

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

    def test_missing_role_defaults_to_employee(self, client, admin_token):
        payload = {k: v for k, v in USER.items() if k != "role"}
        created = {**payload, "_id": "uuid-1", "role": "employee", "password_hash": "hashed", "created_at": "2025-01-01"}
        with patch("app.models.user.UserModel.exists_by_email", return_value=False), \
             patch("app.models.user.UserModel.create", return_value=created):
            res = client.post("/api/users/", json=payload,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["user"]["role"] == "employee"

    def test_invalid_role(self, client, admin_token):
        # "customer" is no longer a valid role in V3
        for bad_role in ["superadmin", "customer"]:
            bad = {**USER, "role": bad_role}
            res = client.post("/api/users/", json=bad,
                              headers={"Authorization": f"Bearer {admin_token}"})
            assert res.status_code == 400
            assert "role" in res.get_json()["errors"]

    def test_invalid_email_format(self, client, admin_token):
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

    def test_name_too_short(self, client, admin_token):
        bad = {**USER, "name": "X"}
        res = client.post("/api/users/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_empty_body(self, client, admin_token):
        res = client.post("/api/users/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_no_content_type(self, client, admin_token):
        res = client.post("/api/users/", data="not json",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 415


class TestGetMe:
    def test_success(self, client, admin_token):
        user = {**USER_DB}
        with patch("app.models.user.UserModel.get_by_id", return_value=user):
            res = client.get("/api/users/me",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert "password_hash" not in res.get_json()["data"]["user"]

    def test_no_token(self, client):
        res = client.get("/api/users/me")
        assert res.status_code == 401

    def test_user_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.get("/api/users/me",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404


class TestGetUser:
    def test_get_existing_user(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB):
            res = client.get("/api/users/uuid-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["_id"] == "uuid-1"

    def test_password_hash_not_returned(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB):
            res = client.get("/api/users/uuid-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert "password_hash" not in res.get_json()["data"]["user"]

    def test_get_nonexistent_user(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.get("/api/users/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/users/uuid-1")
        assert res.status_code == 401

    def test_any_authenticated_user_can_access(self, client, employee_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB):
            res = client.get("/api/users/uuid-1",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200


class TestGetUsers:
    def test_success(self, client, admin_token):
        users = [{"_id": f"uuid-{i}", "name": f"User{i}", "email": f"u{i}@x.com", "role": "employee"} for i in range(3)]
        with patch("app.services.user_service.UserService.get_filtered", return_value=(users, None, False)):
            res = client.get("/api/users/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        body = res.get_json()
        assert len(body["data"]["users"]) == 3
        assert body["data"]["pagination"]["has_more"] is False
        assert body["data"]["pagination"]["next_cursor"] is None

    def test_pagination_structure(self, client, admin_token):
        users = [{"_id": f"uuid-{i}", "name": f"User{i}", "email": f"u{i}@x.com", "role": "employee"} for i in range(5)]
        with patch("app.services.user_service.UserService.get_filtered", return_value=(users, "cursor-abc", True)):
            res = client.get("/api/users/?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"
        assert body["data"]["pagination"]["limit"] == 5

    def test_filter_by_role(self, client, admin_token):
        employees = [{"_id": "uuid-1", "name": "Emp", "email": "emp@x.com", "role": "employee"}]
        with patch("app.services.user_service.UserService.get_filtered", return_value=(employees, None, False)) as mock_svc:
            res = client.get("/api/users/?role=employee",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()
        call_kwargs = mock_svc.call_args
        assert call_kwargs.kwargs.get("role") == "employee" or (call_kwargs.args and "employee" in call_kwargs.args)

    def test_filter_by_email(self, client, admin_token):
        users = [{"_id": "uuid-1", "name": "Rayhan", "email": "rayhan@x.com", "role": "employee"}]
        with patch("app.services.user_service.UserService.get_filtered", return_value=(users, None, False)) as mock_svc:
            res = client.get("/api/users/?email=rayhan",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_empty_result(self, client, admin_token):
        with patch("app.services.user_service.UserService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/users/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["users"] == []

    def test_large_dataset_pagination(self, client, admin_token):
        users = [{"_id": f"uuid-{i}", "name": f"User{i}", "email": f"u{i}@x.com", "role": "employee"} for i in range(100)]
        with patch("app.services.user_service.UserService.get_filtered", return_value=(users, "next-cursor", True)):
            res = client.get("/api/users/?limit=100",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["users"]) == 100

    def test_no_token(self, client):
        res = client.get("/api/users/")
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
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

    def test_limit_zero(self, client, admin_token):
        res = client.get("/api/users/?limit=0",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestUpdateUser:
    def test_success(self, client, admin_token):
        updated = {**USER_DB, "name": "Updated Name"}
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB), \
             patch("app.models.user.UserModel.update", return_value=updated):
            res = client.patch("/api/users/uuid-1", json={"name": "Updated Name"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["name"] == "Updated Name"

    def test_update_role(self, client, admin_token):
        updated = {**USER_DB, "role": "admin"}
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB), \
             patch("app.models.user.UserModel.update", return_value=updated):
            res = client.patch("/api/users/uuid-1", json={"role": "admin"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["role"] == "admin"

    def test_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.patch("/api/users/bad-id", json={"name": "Valid Name"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.patch("/api/users/uuid-1", json={"name": "X"})
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.patch("/api/users/uuid-1", json={"name": "X"},
                           headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_empty_body(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB):
            res = client.patch("/api/users/uuid-1", json={},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_name_too_short(self, client, admin_token):
        res = client.patch("/api/users/uuid-1", json={"name": "X"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "name" in res.get_json()["errors"]

    def test_invalid_role(self, client, admin_token):
        # "customer" is no longer valid in V3
        for bad_role in ["superadmin", "customer"]:
            res = client.patch("/api/users/uuid-1", json={"role": bad_role},
                               headers={"Authorization": f"Bearer {admin_token}"})
            assert res.status_code == 400
            assert "role" in res.get_json()["errors"]


class TestDeleteUser:
    def test_success(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=USER_DB), \
             patch("app.models.pump_employee.PumpEmployeeModel.remove_by_user"), \
             patch("app.models.user.UserModel.delete"):
            res = client.delete("/api/users/uuid-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_not_found(self, client, admin_token):
        with patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.delete("/api/users/bad-id",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.delete("/api/users/uuid-1")
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.delete("/api/users/uuid-1",
                            headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403
