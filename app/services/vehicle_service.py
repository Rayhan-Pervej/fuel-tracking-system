from app.models.user import UserModel
from app.models.vehicle import VehicleModel
from app.constants import encode_cursor, decode_cursor


class VehicleService:

    @staticmethod
    def build_query(user_id=None, vehicle_type=None, search=None, user_email= None):
        query = {}
        if user_id:
            query["user_id"] = user_id
        if vehicle_type:
            query["vehicle_type"] = vehicle_type
        if user_email:
            user = UserModel.get_by_email(user_email)
            query["user_id"] = user["_id"] if user else None
        if search:
            query["vehicle_number"] = {"$regex": search, "$options": "i"}
        return query

    @staticmethod
    def get_filtered(user_id=None, vehicle_type=None, cursor=None, limit=10, search=None, user_email=None):
        query = VehicleService.build_query(user_id=user_id, vehicle_type=vehicle_type, search=search, user_email=user_email)
        after_dt = decode_cursor(cursor) if cursor else None
        rows = VehicleModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return items, next_cursor, has_more
