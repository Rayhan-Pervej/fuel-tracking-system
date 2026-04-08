from unittest.mock import patch


FUEL_PRICE = {
    "_id": "fp-1",
    "fuel_type": "octane",
    "price_per_unit": 125.0,
    "unit": "liter",
    "currency": "BDT",
    "effective_from": "2025-01-01"
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

    def test_no_token(self, client):
        res = client.post("/api/fuel-prices/", json=FUEL_PRICE_PAYLOAD)
        assert res.status_code == 401

    def test_forbidden_non_admin(self, client, employee_token):
        res = client.post("/api/fuel-prices/", json=FUEL_PRICE_PAYLOAD,
                          headers={"Authorization": f"Bearer {employee_token}"})
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

    def test_invalid_date_format(self, client, admin_token):
        bad = {**FUEL_PRICE_PAYLOAD, "effective_from": "01-01-2025"}
        res = client.post("/api/fuel-prices/", json=bad,
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        assert "effective_from" in res.get_json()["errors"]

    def test_missing_fields(self, client, admin_token):
        res = client.post("/api/fuel-prices/", json={},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
        errors = res.get_json()["errors"]
        assert "fuel_type" in errors
        assert "price_per_unit" in errors
        assert "unit" in errors
        assert "effective_from" in errors


class TestGetLatestFuelPrice:
    def test_success(self, client, admin_token):
        with patch("app.models.fuel_price.FuelPriceModel.get_latest", return_value=FUEL_PRICE):
            res = client.get("/api/fuel-prices/latest/octane",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["fuel_price"]["fuel_type"] == "octane"

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

    def test_no_token(self, client):
        res = client.get("/api/fuel-prices/")
        assert res.status_code == 401

    def test_invalid_limit(self, client, admin_token):
        res = client.get("/api/fuel-prices/?limit=abc",
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 400
