from app.extensions import mongo
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError


class UserModel:
    COLLECTION = "users"
    DUMMY_HASH = generate_password_hash("__dummy_password_that_never_matches__")
    @staticmethod
    def collection():
        return mongo.db[UserModel.COLLECTION]
    
    @staticmethod
    def exists_by_email(email: str) -> bool:
        return UserModel.collection().find_one({"email": email}) is not None

    @staticmethod
    def create(name: str, email: str, password: str, role: str,) -> dict:
        user = {
            "_id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
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
    def check_password(user: dict, password: str) -> bool:
        return check_password_hash(user["password_hash"], password)
    
    @staticmethod
    def set_refresh_token(user_id: str, token: str, expires_at: datetime) -> None:
        UserModel.collection().update_one(
            {"_id": user_id},
            {"$set": {"refresh_token": token, "refresh_token_expires_at": expires_at}}
        )

    @staticmethod
    def get_by_refresh_token(token: str) -> dict:
        return UserModel.collection().find_one({
            "refresh_token": token,
            "refresh_token_expires_at": {"$gt": datetime.now(timezone.utc)}
        })

    @staticmethod
    def clear_refresh_token(user_id: str) -> None:
        UserModel.collection().update_one(
            {"_id": user_id},
            {"$unset": {"refresh_token": "", "refresh_token_expires_at": ""}}
        )

    @staticmethod
    def delete(user_id: str) -> None:
        UserModel.collection().delete_one({"_id": user_id})

