from app.extensions import mongo
from datetime import datetime, timezone
import uuid


class VehicleModel:
    COLLECTION = "vehicles"

    @staticmethod
    def collection():
        return mongo.db[VehicleModel.COLLECTION]
    @staticmethod
    def exists_by_number(vehicle_number: str) -> bool:
        return VehicleModel.collection().find_one({"vehicle_number": vehicle_number}) is not None

    @staticmethod
    def create(user_id: str, vehicle_number: str, vehicle_type: str) -> dict:
        vehicle = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "vehicle_number": vehicle_number,
            "type": vehicle_type,
            "created_at": datetime.now(timezone.utc)
        }
        VehicleModel.collection().insert_one(vehicle)
        return vehicle
    
    @staticmethod
    def get_all(page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(VehicleModel.collection().find().sort("created_at", -1).skip(skip).limit(limit))
    
    @staticmethod
    def get_by_id(vehicle_id: str) -> dict:
        return VehicleModel.collection().find_one({"_id": vehicle_id})
    
    @staticmethod
    def get_by_user_id(user_id: str, page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(VehicleModel.collection().find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit))