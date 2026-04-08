from app.extensions import mongo
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash


class UserModel:
    COLLECTION = "users"

    @staticmethod
    def collection():
        return mongo.db[UserModel.COLLECTION]
    
    @staticmethod
    def exists_by_email(email: str) -> bool:
        return UserModel.collection().find_one({"email": email}) is not None

    @staticmethod
    def create(name: str, email: str, password: str, role: str, license: str = None) -> dict:
        user = {
            "_id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": role,
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

    @staticmethod
    def get_by_email(email: str) -> dict:
        return UserModel.collection().find_one({"email": email})
    
    @staticmethod
    def check_password(user: dict, password: str) -> bool:
        return check_password_hash(user["password_hash"], password)