from app.models.fuel_price import FuelPriceModel
from app.constants import encode_cursor, decode_cursor


class FuelPriceService:

    @staticmethod
    def build_query(fuel_type=None):
        query = {}
        if fuel_type:
            query["fuel_type"] = fuel_type
        return query

    @staticmethod
    def get_filtered(fuel_type, cursor, limit):
        query = FuelPriceService.build_query(fuel_type=fuel_type)
        after_dt = decode_cursor(cursor) if cursor else None
        rows = FuelPriceModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return items, next_cursor, has_more
