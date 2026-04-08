from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from app.constants import error_response


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify(error_response(401, "Authorization token is missing")), 401
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
            g.user_id = payload["user_id"]
            g.role = payload.get("role", "customer")
        except jwt.ExpiredSignatureError:
            return jsonify(error_response(401, "Token has expired")), 401
        except jwt.InvalidTokenError:
            return jsonify(error_response(401, "Invalid token")), 401
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.get("role") not in roles:
                return jsonify(error_response(403, "You do not have permission to access this resource")), 403
            return f(*args, **kwargs)
        return decorated
    return decorator