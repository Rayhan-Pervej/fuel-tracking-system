import base64
import json
from functools import wraps
from flask import request, jsonify, g
from app.constants import error_response


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        userinfo_header = request.headers.get("X-Userinfo", "")
        if not userinfo_header:
            return jsonify(error_response(401, "Authorization token is missing")), 401
        try:
            userinfo = json.loads(base64.b64decode(userinfo_header + "==").decode("utf-8"))
            g.user_id = userinfo.get("sub")
            roles = userinfo.get("realm_access", {}).get("roles", [])
            if "admin" in roles:
                g.role = "admin"
            elif "employee" in roles:
                g.role = "employee"
            else:
                g.role = "employee"
        except Exception:
            return jsonify(error_response(401, "Invalid authorization info")), 401
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