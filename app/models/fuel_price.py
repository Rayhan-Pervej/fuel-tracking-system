from app.extensions import mongo
from datetime import datetime, timezone
import uuid


class FuelPriceModel:
    COLLECTION = "fuel_prices"

    @staticmethod
    def collection():
        return mongo.db[FuelPriceModel.COLLECTION]

    @staticmethod
    def create(fuel_type: str, price_per_unit: float, unit: str, effective_from: str) -> dict:
        fuel_price = {
            "_id": str(uuid.uuid4()),
            "fuel_type": fuel_type,
            "price_per_unit": price_per_unit,
            "unit": unit,
            "effective_from": effective_from,
            "created_at": datetime.now(timezone.utc)
        }
        FuelPriceModel.collection().insert_one(fuel_price)
        return fuel_price

    @staticmethod
    def get_latest(fuel_type: str) -> dict:
        return FuelPriceModel.collection().find_one(
            {"fuel_type": fuel_type},
            sort=[("effective_from", -1)]
        )

    @staticmethod
    def get_all(page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(FuelPriceModel.collection().find().sort("created_at", -1).skip(skip).limit(limit))
    
    @staticmethod
    def get_by_id(fuel_price_id: str) -> dict:
        return FuelPriceModel.collection().find_one({"_id": fuel_price_id})

