from app.models.pump import PumpModel
from app.constants import encode_cursor, decode_cursor
import re


class PumpService:

    @staticmethod
    def build_query(location=None):
        query = {}
        if location:
            query["location"] = {"$regex": re.escape(location), "$options": "i"}
        return query

    @staticmethod
    def get_filtered(location, cursor, limit):
        query = PumpService.build_query(location=location)
        after_dt = decode_cursor(cursor) if cursor else None
        rows = PumpModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return items, next_cursor, has_more
