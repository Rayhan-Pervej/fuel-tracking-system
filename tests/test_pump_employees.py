from unittest.mock import patch


PUMP = {"_id": "pump-1", "name": "Test Pump", "location": "Dhaka", "license": "P-123"}
USER = {"_id": "user-1", "name": "Test Employee", "email": "emp@test.com", "role": "employee"}
RECORD = {"_id": "rec-1", "pump_id": "pump-1", "user_id": "user-1", "role": "employee", "added_by": "admin-1"}


class TestAddEmployee:
    def test_success_as_admin(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.create", return_value=RECORD):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201

    def test_success_as_pump_admin(self, client, pump_admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True), \
             patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.create", return_value=RECORD):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "employee"},
                              headers={"Authorization": f"Bearer {pump_admin_token}"})
        assert res.status_code == 201

    def test_forbidden_as_regular_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "employee"},
                              headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.post("/api/pumps/pump-1/employees", json={"user_id": "user-1", "role": "employee"})
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.post("/api/pumps/bad-pump/employees",
                              json={"user_id": "user-1", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_user_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_id", return_value=None):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "bad-user", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_user_not_employee_role(self, client, admin_token):
        customer = {**USER, "role": "customer"}
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_id", return_value=customer), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_already_assigned(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "employee"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 409

    def test_pump_admin_already_exists(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.user.UserModel.get_by_id", return_value=USER), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=True):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "pump_admin"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_role(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"user_id": "user-1", "role": "admin"},
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_missing_user_id(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.post("/api/pumps/pump-1/employees",
                              json={"role": "employee"},
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

    def test_forbidden_as_regular_employee(self, client, employee_token):
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

    def test_cannot_remove_pump_admin(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=True):
            res = client.delete("/api/pumps/pump-1/employees/user-1",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


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

    def test_forbidden_as_regular_employee(self, client, employee_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.is_pump_admin", return_value=False):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "employee"},
                               headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_no_token(self, client):
        res = client.patch("/api/pumps/pump-1/employees/user-1", json={"role": "employee"})
        assert res.status_code == 401

    def test_pump_admin_already_exists(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True), \
             patch("app.models.pump_employee.PumpEmployeeModel.has_pump_admin", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "pump_admin"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_employee_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=False):
            res = client.patch("/api/pumps/pump-1/employees/bad-user",
                               json={"role": "employee"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_invalid_role(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.exists", return_value=True):
            res = client.patch("/api/pumps/pump-1/employees/user-1",
                               json={"role": "superadmin"},
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400


class TestGetEmployees:
    def test_success(self, client, admin_token):
        employees = [RECORD]
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP), \
             patch("app.models.pump_employee.PumpEmployeeModel.get_by_pump", return_value=employees), \
             patch("app.models.pump_employee.PumpEmployeeModel.collection") as mock_col:
            mock_col.return_value.count_documents.return_value = 1
            res = client.get("/api/pumps/pump-1/employees",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        body = res.get_json()
        assert len(body["data"]["employees"]) == 1
        assert body["data"]["pagination"]["total"] == 1

    def test_no_token(self, client):
        res = client.get("/api/pumps/pump-1/employees")
        assert res.status_code == 401

    def test_pump_not_found(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=None):
            res = client.get("/api/pumps/bad-pump/employees",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_invalid_pagination(self, client, admin_token):
        with patch("app.models.pump.PumpModel.get_by_id", return_value=PUMP):
            res = client.get("/api/pumps/pump-1/employees?page=abc",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
