from app.models.user import UserModel
from app.constants import encode_cursor, decode_cursor


class UserService:

    @staticmethod
    def build_query(role=None):
        query = {}
        if role:
            query["role"] = role
        return query

    @staticmethod
    def get_filtered(role, cursor, limit):
        query = UserService.build_query(role=role)
        after_dt = decode_cursor(cursor) if cursor else None
        rows = UserModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return items, next_cursor, has_more
