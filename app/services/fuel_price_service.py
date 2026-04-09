from app.models.fuel_price import FuelPriceModel
from app.constants import encode_cursor, decode_cursor


class FuelPriceService:

    @staticmethod
    def build_query(fuel_type=None, effective_from=None, effective_from_before=None, effective_from_after=None):
        query = {}
        if fuel_type:
            query["fuel_type"] = fuel_type
        if effective_from and not effective_from_after and not effective_from_before:
            query["effective_from"] = effective_from
        if effective_from_after or effective_from_before:
            range_query = {}
            if effective_from_after:
                range_query["$gte"] = effective_from_after
            if effective_from_before:
                range_query["$lte"] = effective_from_before
            query["effective_from"] = range_query

        return query

    @staticmethod
    def get_filtered(fuel_type=None, cursor=None, limit=10, effective_from=None, effective_from_before=None, effective_from_after=None):
        query = FuelPriceService.build_query(
            fuel_type=fuel_type,
            effective_from=effective_from,
            effective_from_before=effective_from_before,
            effective_from_after=effective_from_after
        )
        after_dt = decode_cursor(cursor) if cursor else None
        rows = FuelPriceModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return items, next_cursor, has_more
