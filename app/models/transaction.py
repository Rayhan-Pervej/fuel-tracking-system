from app.extensions import mongo
from datetime import datetime, timezone
import uuid


class TransactionModel:
    COLLECTION = "transactions"

    @staticmethod
    def collection():
        return mongo.db[TransactionModel.COLLECTION]

    @staticmethod
    def create(vehicle_id: str, pump_id: str, fuel_price_id: str, quantity: float, total_price: float) -> dict:
        transaction = {
            "_id": str(uuid.uuid4()),
            "vehicle_id": vehicle_id,
            "pump_id": pump_id,
            "fuel_price_id": fuel_price_id,
            "quantity": quantity,
            "total_price": total_price,
            "created_at": datetime.now(timezone.utc)
        }
        TransactionModel.collection().insert_one(transaction)
        return transaction

    @staticmethod
    def get_all(page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(TransactionModel.collection().find().sort("created_at", -1).skip(skip).limit(limit))

    @staticmethod
    def get_by_id(transaction_id: str) -> dict:
        return TransactionModel.collection().find_one({"_id": transaction_id})

    @staticmethod
    def get_by_vehicle(vehicle_id: str, page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(TransactionModel.collection().find({"vehicle_id": vehicle_id}).sort("created_at", -1).skip(skip).limit(limit))

    @staticmethod
    def get_by_pump(pump_id: str, page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(TransactionModel.collection().find({"pump_id": pump_id}).sort("created_at", -1).skip(skip).limit(limit))
