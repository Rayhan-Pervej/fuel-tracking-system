import base64
from datetime import datetime


FUEL_TYPES = ["octane", "diesel", "petrol"]
CURRENCIES = ["BDT", "USD", "EUR", "GBP"]
UNITS = ["liter", "gallon"]
ROLES = ["admin", "employee"]
PUMP_EMPLOYEE_ROLES = ["pump_admin", "employee"]


def get_cursor_params(request):
    try:
        limit = min(int(request.args.get('limit', 10)), 100)
        if limit < 1:
            raise ValueError
    except (ValueError, TypeError):
        return None, None
    cursor = request.args.get('cursor', None)
    return cursor, limit


def encode_cursor(dt: datetime) -> str:
    return base64.b64encode(dt.isoformat().encode()).decode()


def decode_cursor(cursor: str) -> datetime:
    try:
        iso = base64.b64decode(cursor.encode()).decode()
        return datetime.fromisoformat(iso)
    except Exception:
        return None


def success_response(message, data):
    return {"status": 200, "message": message, "data": data}


def created_response(message, data):
    return {"status": 201, "message": message, "data": data}


def cursor_response(message, key, items, next_cursor, has_more, limit):
    return {
        "status": 200,
        "message": message,
        "data": {
            key: items,
            "pagination": {
                "limit": limit,
                "next_cursor": next_cursor,
                "has_more": has_more
            }
        }
    }


def error_response(status, message, errors=None):
    return {"status": status, "message": message, "errors": errors or {}}
