import math


FUEL_TYPES = ["octane", "diesel", "petrol"]


def get_pagination_params(request):
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 100)
        if page < 1 or limit < 1:
            raise ValueError
    except (ValueError, TypeError):
        return None, None
    return page, limit



def success_response(message, data):
    return {"status": 200, "message": message, "data": data}


def created_response(message, data):
    return {"status": 201, "message": message, "data": data}


def paginated_response(message, key, items, page, limit, total):
    return {
        "status": 200,
        "message": message,
        "data": {
            key: items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": math.ceil(total / limit) if total > 0 else 0
            }
        }
    }


def error_response(status, message, errors=None):
    return {"status": status, "message": message, "errors": errors or {}}