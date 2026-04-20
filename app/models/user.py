from app.extensions import mongo
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError


class UserModel:
    COLLECTION = "users"
    @staticmethod
    def collection():
        return mongo.db[UserModel.COLLECTION]
    
    @staticmethod
    def exists_by_email(email: str) -> bool:
        return UserModel.collection().find_one({"email": email}) is not None

    @staticmethod
    def create(name: str, email: str, role: str, user_id: str) -> dict:
        user = {
            "_id": user_id,
            "name": name,
            "email": email,
            "role": role,
            "created_at": datetime.now(timezone.utc)
        }
        try:
            UserModel.collection().insert_one(user)
        except DuplicateKeyError:
            raise ValueError("User with this email already exists")
        return user
    
    @staticmethod
    def update(user_id: str, data: dict) -> dict:
        UserModel.collection().update_one({"_id": user_id}, {"$set": data})
        return UserModel.get_by_id(user_id)

    @staticmethod
    def get_page(query: dict, after_dt: datetime = None, limit: int = 10) -> list:
        if after_dt:
            query = {**query, "created_at": {"$lt": after_dt}}
        return list(UserModel.collection().find(query).sort("created_at", -1).limit(limit + 1))
    
    @staticmethod
    def get_by_id(user_id: str) -> dict:
        return UserModel.collection().find_one({"_id": user_id})

    @staticmethod
    def get_by_email(email: str) -> dict:
        return UserModel.collection().find_one({"email": email})
    

    @staticmethod
    def delete(user_id: str) -> None:
        UserModel.collection().delete_one({"_id": user_id})

