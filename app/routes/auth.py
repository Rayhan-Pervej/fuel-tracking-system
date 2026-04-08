from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from app.models.user import UserModel
from app.schemas.auth import LoginSchema
from app.schemas.user import UserSchema
from app.constants import error_response, success_response, created_response
import jwt
from datetime import datetime, timezone, timedelta


auth_bp = Blueprint("auth", __name__)
schema = LoginSchema()
register_schema = UserSchema()

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    user = UserModel.get_by_email(data['email'])
    if not user or not UserModel.check_password(user, data['password']):
        return jsonify(error_response(401, "Invalid email or password")), 401
    token = jwt.encode({
        "user_id": user["_id"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(days=current_app.config["JWT_EXPIRY_DAYS"])
    }, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
    return jsonify(success_response("Login successful", {"token": token})), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = register_schema.load(request.get_json() or {})
        if data["role"] not in ["customer"]:
            return jsonify(error_response(403, "Cannot self-register as admin or employee")), 403
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    
    if UserModel.exists_by_email(data['email']):
        return jsonify(error_response(409, "User with this email already exists")), 409
    
    user = UserModel.create(**data)
    user.pop("password_hash", None)

    return jsonify(created_response("User registered successfully", {"user": user})), 201