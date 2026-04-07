from app.extensions import mongo
from datetime import datetime, timezone
import uuid


class UserModel:
    COLLECTION = "users"

    @staticmethod
    def collection():
        return mongo.db[UserModel.COLLECTION]
    
    @staticmethod
    def exists_by_license(license: str) -> bool:
        return UserModel.collection().find_one({"license": license}) is not None

    @staticmethod
    def create(name: str, license: str) -> dict:
        user = {
            "_id": str(uuid.uuid4()),
            "name": name,
            "license": license,
            "created_at": datetime.now(timezone.utc)
        }
        UserModel.collection().insert_one(user)
        return user

    @staticmethod
    def get_all(page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(UserModel.collection().find().sort("created_at", -1).skip(skip).limit(limit))

    @staticmethod
    def get_by_id(user_id: str) -> dict:
        return UserModel.collection().find_one({"_id": user_id})
