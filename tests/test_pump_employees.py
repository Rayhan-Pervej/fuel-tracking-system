from unittest.mock import patch
from datetime import datetime, timezone


PUMP = {"_id": "pump-1", "name": "Test Pump", "location": "Dhaka", "license": "P-123"}
USER = {"_id": "user-1", "name": "Test Employee", "email": "emp@test.com", "role": "employee"}
RECORD = {
    "_id": "rec-1",
    "pump_id": "pump-1",
    "user_id": "user-1",
    "role": "employee",
    "added_by": "admin-1",
    "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc)
}


class TestGetMyPump:
    def test_success_as_employee(self, client, employee_token):
        with patch("app.models.pump_employee.PumpEmployeeModel.get_by_user", return_value=RECORD):
            res = client.get("/api/pumps/me/pump",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["pump"]["_id"] == "rec-1"

    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.pump_employee.PumpEmployeeModel.get_by_user", return_value=RECORD):
            res = client.get("/api/pumps/me/pump",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200


    def test_no_token(self, client):
        res = client.get("/api/pumps/me/pump")
        assert res.status_code == 401

    def test_returns_404_when_no_assignment(self, client, employee_token):
        with patch("app.models.pump_employee.PumpEmployeeModel.get_by_user", return_value=None):
            res = client.get("/api/pumps/me/pump",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 404


class TestAddEmployee:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_assigned_anywhere", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.create", return_value=RECORD):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["employee"]["_id"] == "rec-1"

    def test_success_as_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_assigned_anywhere", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.create", return_value=RECORD):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 201

    def test_forbidden_regular_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False):
            res = client.post("/api/pumps/pump-1/employees",
                            json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403


    def test_no_token(self, client):
        res = client.post("/api/pumps/pump-1/employees",
                          json={"mode": "existing", "email": "emp@test.com", "role": "employee"})
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.post("/api/pumps/bad-pump/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_user_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=None):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "notfound@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_create_new_user_and_assign_success(self, client, admin_token):
        created_user = {"_id": "user-new", "name": "New Emp", "email": "new@test.com", "role": "employee"}
        created_record = {**RECORD, "_id": "rec-new", "user_id": "user-new"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=None), \
             patch("app.models.user.UserModel.create", return_value=created_user), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_assigned_anywhere", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.create", return_value=created_record):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "new", "name": "New Emp", "email": "new@test.com", "password": "secret123", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["employee"]["user_id"] == "user-new"

    def test_new_mode_missing_name_password(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=None):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "new", "email": "new@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_new_mode_user_already_exists(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=USER):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "new", "name": "Existing", "email": "emp@test.com", "password": "secret123", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_pump_admin_cannot_create_new_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.models.user.UserModel.get_by_email", return_value=None):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "new", "name": "New PA", "email": "pa@test.com", "password": "secret123", "role": "pump_admin"},
                              headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 403

    def test_already_assigned_to_this_pump(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_already_assigned_to_another_pump(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_assigned_anywhere", return_value=True):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_user_not_employee_role(self, client, admin_token):
        admin_user = {**USER, "role": "admin"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=admin_user), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_assigned_anywhere", return_value=False):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_pump_admin_already_exists(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_email", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_assigned_anywhere", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=True):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "pump_admin"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_role(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com", "role": "admin"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_missing_email(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_missing_role(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"mode": "existing", "email": "emp@test.com"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_missing_mode(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"email": "emp@test.com", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestRemoveEmployee:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.remove", return_value=True):
            res = client.delete("/api/pumps/pump-1/employees/user-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_success_as_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", side_effect=[True, False]), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.remove", return_value=True):
            res = client.delete("/api/pumps/pump-1/employees/user-1",
                                headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 200

    def test_forbidden_regular_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False):
            res = client.delete("/api/pumps/pump-1/employees/user-1",
                                headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.delete("/api/pumps/pump-1/employees/user-1")
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.delete("/api/pumps/bad-pump/employees/user-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_employee_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.delete("/api/pumps/pump-1/employees/bad-user",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_cannot_remove_pump_admin_as_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", side_effect=[True, True]):
            res = client.delete("/api/pumps/pump-1/employees/user-1",
                                headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 400

    def test_admin_can_remove_pump_admin(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.remove", return_value=True):
            res = client.delete("/api/pumps/pump-1/employees/user-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200


class TestUpdateEmployeeRole:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.update_role", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "pump_admin"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_success_as_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.update_role", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "employee"},
                               headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 200

    def test_forbidden_regular_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "employee"},
                               headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.patch("/api/pumps/pump-1/employees/user-1", json={"role": "employee"})
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.patch("/api/pumps/bad-pump/employees/user-1",
                               json={"role": "employee"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_employee_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.patch("/api/pumps/pump-1/employees/bad-user",
                               json={"role": "employee"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_pump_admin_already_exists_as_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "pump_admin"},
                               headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 400

    def test_admin_can_override_pump_admin(self, client, admin_token):
        # admin can promote even if pump_admin exists
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.update_role", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "pump_admin"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200

    def test_invalid_role(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "superadmin"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_missing_role(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestGetEmployees:
    def test_success_as_admin(self, client, admin_token):
        employees = [RECORD]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.get_by_pump", return_value=employees):
            res = client.get("/api/pumps/pump-1/employees",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        body = res.get_json()
        assert len(body["data"]["employees"]) == 1
        assert body["data"]["pagination"]["has_more"] is False

    def test_success_as_assigned_employee(self, client, employee_token):
        employees = [RECORD]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.get_by_pump", return_value=employees):
            res = client.get("/api/pumps/pump-1/employees",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_forbidden_unassigned_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.get("/api/pumps/pump-1/employees",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.get("/api/pumps/pump-1/employees")
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.get("/api/pumps/bad-pump/employees",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_empty_result(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.get_by_pump", return_value=[]):
            res = client.get("/api/pumps/pump-1/employees",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["employees"] == []

    def test_invalid_limit(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/pumps/pump-1/employees?limit=abc",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_pagination_has_more(self, client, admin_token):
        # Return limit+1 records to simulate has_more=True
        employees = [RECORD] * 11
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.get_by_pump", return_value=employees):
            res = client.get("/api/pumps/pump-1/employees?limit=10",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert len(body["data"]["employees"]) == 10
