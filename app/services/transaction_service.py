from datetime import datetime, timezone
from app.models.transaction import TransactionModel
from app.constants import encode_cursor, decode_cursor


class TransactionService:

    @staticmethod
    def build_query(from_date=None, to_date=None, vehicle_id=None, pump_id=None):
        query = {}
        if vehicle_id:
            query["vehicle_id"] = vehicle_id
        if pump_id:
            query["pump_id"] = pump_id
        if from_date and to_date:
            query["created_at"] = {
                "$gte": datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc),
                "$lte": datetime.strptime(to_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            }
        return query

    @staticmethod
    def get_filtered(from_date, to_date, vehicle_id, pump_id, cursor, limit):
        query = TransactionService.build_query(from_date, to_date, vehicle_id, pump_id)
        after_dt = decode_cursor(cursor) if cursor else None
        rows = TransactionModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return items, next_cursor, has_more
