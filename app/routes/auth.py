import uuid
from flask import Blueprint, request, jsonify, current_app, g
from marshmallow import ValidationError
from app.models.user import UserModel
from app.schemas.auth import LoginSchema
from app.schemas.user import UserSchema
from app.constants import error_response, success_response, created_response
import jwt
from datetime import datetime, timezone, timedelta
from app.extensions import limiter
from app.middleware.auth import require_auth
auth_bp = Blueprint("auth", __name__)
schema = LoginSchema()
register_schema = UserSchema()

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    user = UserModel.get_by_email(data['email'])
    if user:
        password_valid = UserModel.check_password(user, data['password'])
    else:
        UserModel.check_password({"password_hash": UserModel.DUMMY_HASH}, data['password'])
        password_valid = False
    if not password_valid:
        return jsonify(error_response(401, "Invalid email or password")), 401

    access_token = jwt.encode({
        "user_id": user["_id"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=current_app.config["JWT_ACCESS_EXPIRY_MINUTES"])
    }, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

    refresh_token = str(uuid.uuid4())
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=current_app.config["JWT_REFRESH_EXPIRY_DAYS"])
    UserModel.set_refresh_token(user["_id"], refresh_token, refresh_expires_at)

    return jsonify(success_response("Login successful", {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    })), 200


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    try:
        data = register_schema.load(request.get_json() or {})
        if data["role"] not in ["customer"]:
            return jsonify(error_response(403, "Cannot self-register as admin or employee")), 403
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    
    if UserModel.exists_by_email(data['email']):
        return jsonify(error_response(409, "User with this email already exists")), 409
    
    try:
        user = UserModel.create(**data)
    except ValueError as e:
        return jsonify(error_response(409, str(e))), 409
    user.pop("password_hash", None)

    return jsonify(created_response("User registered successfully", {"user": user})), 201


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json() or {}
    token = data.get('refresh_token')
    if not token:
        return jsonify(error_response(400, "refresh_token is required")), 400

    user = UserModel.get_by_refresh_token(token)
    if not user:
        return jsonify(error_response(401, "Invalid or expired refresh token")), 401

    access_token = jwt.encode({
        "user_id": user["_id"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=current_app.config["JWT_ACCESS_EXPIRY_MINUTES"])
    }, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

    return jsonify(success_response("Token refreshed", {
        "access_token": access_token,
        "token_type": "Bearer"
    })), 200


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    data = request.get_json() or {}
    token = data.get('refresh_token')
    if not token:
        return jsonify(error_response(400, "refresh_token is required")), 400
    UserModel.clear_refresh_token(g.user_id)
    return jsonify(success_response("Logged out successfully", {})), 200
