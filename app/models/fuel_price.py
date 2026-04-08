from app.extensions import mongo
from datetime import datetime, timezone
import uuid


class FuelPriceModel:
    COLLECTION = "fuel_prices"

    @staticmethod
    def collection():
        return mongo.db[FuelPriceModel.COLLECTION]

    @staticmethod
    def create(fuel_type: str, price_per_unit: float, unit: str, currency: str, effective_from: str) -> dict:
        fuel_price = {
            "_id": str(uuid.uuid4()),
            "fuel_type": fuel_type,
            "price_per_unit": price_per_unit,
            "unit": unit,
            "currency": currency,
            "effective_from": effective_from,
            "created_at": datetime.now(timezone.utc)
        }
        FuelPriceModel.collection().insert_one(fuel_price)
        return fuel_price

    @staticmethod
    def get_latest(fuel_type: str, session=None) -> dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return FuelPriceModel.collection().find_one(
            {"fuel_type": fuel_type, "effective_from": {"$lte": today}},
            sort=[("effective_from", -1)],
            session=session
        )
    
    @staticmethod
    def get_page(query: dict, after_dt: datetime = None, limit: int = 10) -> list:
        if after_dt:
            query = {**query, "created_at": {"$lt": after_dt}}
        return list(FuelPriceModel.collection().find(query).sort("created_at", -1).limit(limit + 1))

    @staticmethod
    def get_by_id(fuel_price_id: str) -> dict:
        return FuelPriceModel.collection().find_one({"_id": fuel_price_id})
