from unittest.mock import patch


FUEL_PRICE = {
    "_id": "fp-1",
    "fuel_type": "octane",
    "price_per_unit": 125.0,
    "unit": "liter",
    "currency": "BDT",
    "effective_from": "2025-01-01",
    "created_at": "2025-01-01"
}

FUEL_PRICE_PAYLOAD = {
    "fuel_type": "octane",
    "price_per_unit": 125.0,
    "unit": "liter",
    "effective_from": "2025-01-01"
}


class TestCreateFuelPrice:
    def test_success(self, client, admin_token):
        with patch("app.models.fuel_price.FuelPriceModel.create", return_value=FUEL_PRICE):
            res = client.post("/api/fuel-prices/", json=FUEL_PRICE_PAYLOAD,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["fuel_price"]["_id"] == "fp-1"

    def test_success_with_optional_currency(self, client, admin_token):
        payload = {**FUEL_PRICE_PAYLOAD, "currency": "USD"}
        created = {**FUEL_PRICE, "currency": "USD"}
        with patch("app.models.fuel_price.FuelPriceModel.create", return_value=created):
            res = client.post("/api/fuel-prices/", json=payload,
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["fuel_price"]["currency"] == "USD"

    def test_no_token(self, client):
        res = client.post("/api/fuel-prices/", json=FUEL_PRICE_PAYLOAD)
        assert res.status_code == 401

    def test_forbidden_employee(self, client, employee_token):
        res = client.post("/api/fuel-prices/", json=FUEL_PRICE_PAYLOAD,
                          headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 403

    def test_forbidden_customer(self, client, customer_token):
        res = client.post("/api/fuel-prices/", json=FUEL_PRICE_PAYLOAD,
                          headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 403

    def test_invalid_fuel_type(self, client, admin_token):
        bad = {**FUEL_PRICE_PAYLOAD, "fuel_type": "kerosene"}
        res = client.post("/api/fuel-prices/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "fuel_type" in res.get_json()["errors"]

    def test_invalid_unit(self, client, admin_token):
        bad = {**FUEL_PRICE_PAYLOAD, "unit": "barrel"}
        res = client.post("/api/fuel-prices/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "unit" in res.get_json()["errors"]

    def test_invalid_currency(self, client, admin_token):
        bad = {**FUEL_PRICE_PAYLOAD, "currency": "YEN"}
        res = client.post("/api/fuel-prices/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "currency" in res.get_json()["errors"]

    def test_invalid_date_format(self, client, admin_token):
        bad = {**FUEL_PRICE_PAYLOAD, "effective_from": "01-01-2025"}
        res = client.post("/api/fuel-prices/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "effective_from" in res.get_json()["errors"]

    def test_price_too_low(self, client, admin_token):
        bad = {**FUEL_PRICE_PAYLOAD, "price_per_unit": 0.0}
        res = client.post("/api/fuel-prices/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "price_per_unit" in res.get_json()["errors"]

    def test_missing_all_required_fields(self, client, admin_token):
        res = client.post("/api/fuel-prices/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        errors = res.get_json()["errors"]
        assert "fuel_type" in errors
        assert "price_per_unit" in errors
        assert "unit" in errors
        assert "effective_from" in errors

    def test_all_fuel_types_valid(self, client, admin_token):
        for ftype in ["octane", "diesel", "petrol"]:
            payload = {**FUEL_PRICE_PAYLOAD, "fuel_type": ftype}
            created = {**FUEL_PRICE, "fuel_type": ftype}
            with patch("app.models.fuel_price.FuelPriceModel.create", return_value=created):
                res = client.post("/api/fuel-prices/", json=payload,
                                  headers={"Authorization": f"Bearer {admin_token}"})
            assert res.status_code == 201, f"fuel_type '{ftype}' should be valid"

    def test_all_units_valid(self, client, admin_token):
        for unit in ["liter", "gallon"]:
            payload = {**FUEL_PRICE_PAYLOAD, "unit": unit}
            created = {**FUEL_PRICE, "unit": unit}
            with patch("app.models.fuel_price.FuelPriceModel.create", return_value=created):
                res = client.post("/api/fuel-prices/", json=payload,
                                  headers={"Authorization": f"Bearer {admin_token}"})
            assert res.status_code == 201, f"unit '{unit}' should be valid"


class TestGetLatestFuelPrice:
    def test_success(self, client, admin_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE):
            res = client.get("/api/fuel-prices/latest/octane",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["fuel_price"]["fuel_type"] == "octane"

    def test_success_as_employee(self, client, employee_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE):
            res = client.get("/api/fuel-prices/latest/octane",
                             headers={"Authorization": f"Bearer {employee_token}"})
        assert res.status_code == 200

    def test_success_as_customer(self, client, customer_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE):
            res = client.get("/api/fuel-prices/latest/octane",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_not_found(self, client, admin_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=None):
            res = client.get("/api/fuel-prices/latest/diesel",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/fuel-prices/latest/octane")
        assert res.status_code == 401


class TestGetFuelPrice:
    def test_success(self, client, admin_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=FUEL_PRICE):
            res = client.get("/api/fuel-prices/fp-1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["fuel_price"]["_id"] == "fp-1"

    def test_success_as_any_authenticated_user(self, client, customer_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=FUEL_PRICE):
            res = client.get("/api/fuel-prices/fp-1",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_not_found(self, client, admin_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_by_id", return_value=None):
            res = client.get("/api/fuel-prices/bad-id",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 404

    def test_no_token(self, client):
        res = client.get("/api/fuel-prices/fp-1")
        assert res.status_code == 401


class TestGetAllFuelPrices:
    def test_success(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)):
            res = client.get("/api/fuel-prices/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["fuel_prices"]) == 1

    def test_accessible_by_any_authenticated_user(self, client, customer_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)):
            res = client.get("/api/fuel-prices/",
                             headers={"Authorization": f"Bearer {customer_token}"})
        assert res.status_code == 200

    def test_filter_by_fuel_type(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)) as mock_svc:
            res = client.get("/api/fuel-prices/?fuel_type=octane",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_effective_from_exact(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)) as mock_svc:
            res = client.get("/api/fuel-prices/?effective_from=2025-01-01",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_effective_from_after(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)) as mock_svc:
            res = client.get("/api/fuel-prices/?effective_from_after=2024-01-01",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_effective_from_before(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)) as mock_svc:
            res = client.get("/api/fuel-prices/?effective_from_before=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_by_date_range(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)) as mock_svc:
            res = client.get("/api/fuel-prices/?effective_from_after=2024-01-01&effective_from_before=2025-12-31",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_filter_fuel_type_and_date_range(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([FUEL_PRICE], None, False)) as mock_svc:
            res = client.get("/api/fuel-prices/?fuel_type=octane&effective_from_after=2024-01-01",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        mock_svc.assert_called_once()

    def test_empty_result(self, client, admin_token):
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=([], None, False)):
            res = client.get("/api/fuel-prices/",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["fuel_prices"] == []

    def test_pagination_structure(self, client, admin_token):
        prices = [FUEL_PRICE] * 5
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=(prices, "cursor-abc", True)):
            res = client.get("/api/fuel-prices/?limit=5",
                             headers={"Authorization": f"Bearer {admin_token}"})
        body = res.get_json()
        assert body["data"]["pagination"]["has_more"] is True
        assert body["data"]["pagination"]["next_cursor"] == "cursor-abc"
        assert body["data"]["pagination"]["limit"] == 5

    def test_large_dataset(self, client, admin_token):
        prices = [{"_id": f"fp-{i}", **FUEL_PRICE_PAYLOAD, "currency": "BDT"} for i in range(100)]
        with patch("app.services.fuel_price_service.FuelPriceService.get_filtered", return_value=(prices, "next", True)):
            res = client.get("/api/fuel-prices/?limit=100",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.get_json()["data"]["fuel_prices"]) == 100

    def test_no_token(self, client):
        res = client.get("/api/fuel-prices/")
        assert res.status_code == 401

    def test_invalid_limit(self, client, admin_token):
        res = client.get("/api/fuel-prices/?limit=abc",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400

    def test_invalid_negative_limit(self, client, admin_token):
        res = client.get("/api/fuel-prices/?limit=-1",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
