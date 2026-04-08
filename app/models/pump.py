from app.extensions import mongo
from datetime import datetime, timezone
import uuid
from pymongo.errors import DuplicateKeyError


class PumpModel:
    COLLECTION = "pumps"

    @staticmethod
    def collection():
        return mongo.db[PumpModel.COLLECTION]
    
    @staticmethod
    def exists_by_license(license: str) -> bool:
        return PumpModel.collection().find_one({"license": license}) is not None

    
    @staticmethod
    def create(name: str, location: str, license: str) -> dict:
        pump = {
            "_id": str(uuid.uuid4()),
            "name": name,
            "location": location,
            "license": license,
            "created_at": datetime.now(timezone.utc)
        }
        try:
            PumpModel.collection().insert_one(pump)
        except DuplicateKeyError:
            raise ValueError("Pump with this license already exists")
        return pump
    @staticmethod
    def update(pump_id: str, data: dict) -> dict:
        PumpModel.collection().update_one({"_id": pump_id}, {"$set": data})
        return PumpModel.get_by_id(pump_id)
    
    @staticmethod
    def get_page(query: dict, after_dt: datetime = None, limit: int = 10) -> list:
        if after_dt:
            query = {**query, "created_at": {"$lt": after_dt}}
        return list(PumpModel.collection().find(query).sort("created_at", -1).limit(limit + 1))

    @staticmethod
    def get_by_id(pump_id: str) -> dict:
        return PumpModel.collection().find_one({"_id": pump_id})
    

    @staticmethod
    def delete(pump_id: str) -> None:
        PumpModel.collection().delete_one({"_id": pump_id})
