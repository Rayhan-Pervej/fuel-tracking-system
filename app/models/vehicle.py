from app.extensions import mongo
from datetime import datetime, timezone
import uuid
from pymongo.errors import DuplicateKeyError


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
            "vehicle_type": vehicle_type,
            "created_at": datetime.now(timezone.utc)
        }
        try:
            VehicleModel.collection().insert_one(vehicle)
        except DuplicateKeyError:
            raise ValueError("Vehicle with this number already exists")
        return vehicle
    @staticmethod
    def update(vehicle_id: str, data: dict) -> dict:
        VehicleModel.collection().update_one({"_id": vehicle_id}, {"$set": data})
        return VehicleModel.get_by_id(vehicle_id)

    @staticmethod
    def get_page(query: dict, after_dt: datetime = None, limit: int = 10) -> list:
        if after_dt:
            query = {**query, "created_at": {"$lt": after_dt}}
        return list(VehicleModel.collection().find(query).sort("created_at", -1).limit(limit + 1))

    @staticmethod
    def get_by_id(vehicle_id: str) -> dict:
        return VehicleModel.collection().find_one({"_id": vehicle_id})
    
    @staticmethod
    def delete_by_user(user_id: str) -> None:
        VehicleModel.collection().delete_many({"user_id": user_id})

    @staticmethod
    def delete(vehicle_id: str) -> None:
        VehicleModel.collection().delete_one({"_id": vehicle_id})

    @staticmethod
    def get_ids_by_number(vehicle_number: str) -> list:
        return [v["_id"] for v in VehicleModel.collection().find(
            {"vehicle_number": {"$regex": vehicle_number, "$options": "i"}},
            {"_id": 1}
        )]
