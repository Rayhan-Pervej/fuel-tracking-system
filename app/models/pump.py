from app.extensions import mongo
from datetime import datetime, timezone
import uuid


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
        PumpModel.collection().insert_one(pump)
        return pump
    
    @staticmethod
    def get_all(page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(PumpModel.collection().find().sort("created_at", -1).skip(skip).limit(limit))
    
    @staticmethod
    def get_by_id(pump_id: str) -> dict:
        return PumpModel.collection().find_one({"_id": pump_id})