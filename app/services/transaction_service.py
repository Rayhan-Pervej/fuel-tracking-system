from datetime import datetime, timezone
from app.models.transaction import TransactionModel
from app.models.vehicle import VehicleModel
from app.models.pump import PumpModel
from app.models.fuel_price import FuelPriceModel
from app.constants import encode_cursor, decode_cursor


class TransactionService:

    @staticmethod
    def build_query(from_date=None, to_date=None, vehicle_id=None, pump_id=None, fuel_type=None):
        query = {}
        if vehicle_id:
            query["vehicle_id"] = vehicle_id
        if pump_id:
            query["pump_id"] = pump_id
        if fuel_type:
            fuel_price_ids =[fp["_id"] for fp in FuelPriceModel.get_by_fuel_type(fuel_type)]
            query["fuel_price_id"] = {"$in": fuel_price_ids}    
        if from_date and to_date:
            query["created_at"] = {
                "$gte": datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc),
                "$lte": datetime.strptime(to_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            }
        return query

    @staticmethod
    def enrich(transactions: list) -> list:
        for t in transactions:
            vehicle = VehicleModel.get_by_id(t.get("vehicle_id"))
            t["vehicle_number"] = vehicle["vehicle_number"] if vehicle else None

            pump = PumpModel.get_by_id(t.get("pump_id"))
            t["pump_name"] = pump["name"] if pump else None

            fuel_price = FuelPriceModel.get_by_id(t.get("fuel_price_id"))
            if fuel_price:
                t["fuel_type"] = fuel_price["fuel_type"]
                t["unit"] = fuel_price["unit"]
                t["currency"] = fuel_price["currency"]
            else:
                t["fuel_type"] = None
                t["unit"] = None
                t["currency"] = None
        return transactions

    @staticmethod
    def get_filtered(from_date, to_date, vehicle_id, pump_id, fuel_type, cursor, limit):
        query = TransactionService.build_query(from_date, to_date, vehicle_id, pump_id, fuel_type)
        after_dt = decode_cursor(cursor) if cursor else None
        rows = TransactionModel.get_page(query, after_dt=after_dt, limit=limit)
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]["created_at"]) if (has_more and items) else None
        return TransactionService.enrich(items), next_cursor, has_more
