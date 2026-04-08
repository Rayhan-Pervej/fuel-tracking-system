from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.user import UserModel
from app.schemas.user import UserSchema, UserUpdateSchema
from app.services.user_service import UserService
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response
from app.middleware.auth import require_auth, require_role

user_bp = Blueprint("user", __name__)
schema = UserSchema()
update_schema = UserUpdateSchema()

@user_bp.route('/', methods=['POST'])
@require_auth
@require_role("admin")
def create_user():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    if UserModel.exists_by_email(data['email']):
        return jsonify(error_response(409, "User with this email already exists")), 409
    try:
        user = UserModel.create(**data)
    except ValueError as e:
        return jsonify(error_response(409, str(e))), 409
    user.pop("password_hash", None)
    return jsonify(created_response("User created successfully", {"user": user})), 201


@user_bp.route('/', methods=['GET'])
@require_auth
@require_role("admin")
def get_users():
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    users, next_cursor, has_more = UserService.get_filtered(
        role=request.args.get("role"),
        cursor=cursor,
        limit=limit
    )
    for user in users:
        user.pop("password_hash", None)
        user.pop("refresh_token", None)
        user.pop("refresh_token_expires_at", None)
    return jsonify(cursor_response("Users retrieved successfully", "users", users, next_cursor, has_more, limit)), 200

@user_bp.route('/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    user = UserModel.get_by_id(user_id)
    if not user:
        return jsonify(error_response(404, "User not found")), 404
    user.pop("password_hash", None)
    user.pop("refresh_token", None)
    user.pop("refresh_token_expires_at", None)
    return jsonify(success_response("User retrieved successfully", {"user": user})), 200


@user_bp.route('/<user_id>', methods=['PATCH'])
@require_auth
@require_role("admin")
def update_user(user_id):
    try:
        data = update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if not data:
        return jsonify(error_response(400, "No fields provided to update")), 400

    user = UserModel.get_by_id(user_id)
    if not user:
        return jsonify(error_response(404, "User not found")), 404

    updated = UserModel.update(user_id, data)
    updated.pop("password_hash", None)
    updated.pop("refresh_token", None)
    updated.pop("refresh_token_expires_at", None)
    return jsonify(success_response("User updated successfully", {"user": updated})), 200


