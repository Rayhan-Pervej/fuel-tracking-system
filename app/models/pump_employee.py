from app.extensions import mongo
from datetime import datetime, timezone
import uuid
from app.constants import PUMP_EMPLOYEE_ROLES

class PumpEmployeeModel:
    COLLECTION = "pump_employees"

    @staticmethod
    def collection():
        return mongo.db[PumpEmployeeModel.COLLECTION]
    
    @staticmethod
    def exists(pump_id: str, user_id: str) -> bool:
        return PumpEmployeeModel.collection().find_one({"pump_id": pump_id, "user_id": user_id}) is not None
    
    @staticmethod
    def has_pump_admin(pump_id: str) -> bool:
        return PumpEmployeeModel.collection().find_one({"pump_id": pump_id, "role": "pump_admin"}) is not None
    
    @staticmethod
    def get_pump_admin(pump_id: str) -> dict:
        return PumpEmployeeModel.collection().find_one({"pump_id": pump_id, "role": "pump_admin"})
    
    @staticmethod
    def is_pump_admin(pump_id: str, user_id: str) -> bool:
        return PumpEmployeeModel.collection().find_one({"pump_id": pump_id, "user_id": user_id, "role": "pump_admin"}) is not None
    
    @staticmethod
    def create(pump_id: str, user_id: str, added_by: str, role: str) -> dict:
        if role not in PUMP_EMPLOYEE_ROLES:
            raise ValueError("Invalid role")

        record = {
            "_id": str(uuid.uuid4()),
            "pump_id": pump_id,
            "user_id": user_id,
            "role": role,
            "added_by": added_by,         
            "created_at": datetime.now(timezone.utc)
        }

        PumpEmployeeModel.collection().insert_one(record)
        return record
    
    @staticmethod
    def update_role(pump_id: str, user_id: str, role: str) -> bool:
        if role not in PUMP_EMPLOYEE_ROLES:
            raise ValueError("Invalid role")
        result = PumpEmployeeModel.collection().update_one(
            {"pump_id": pump_id, "user_id": user_id},
            {"$set": {"role": role}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def remove(pump_id: str, user_id: str) -> bool:
        result = PumpEmployeeModel.collection().delete_one({"pump_id": pump_id, "user_id": user_id})
        return result.deleted_count > 0
    
    @staticmethod
    def get_by_pump(pump_id: str, page: int = 1, limit: int = 10) -> list:
        skip = (page - 1) * limit
        return list(PumpEmployeeModel.collection().find({"pump_id": pump_id}).sort("created_at", -1).skip(skip).limit(limit))
