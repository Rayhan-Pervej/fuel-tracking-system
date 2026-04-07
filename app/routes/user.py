from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.user import UserModel
from app.schemas.user import UserSchema
from app.constants import get_pagination_params, success_response, created_response, paginated_response, error_response

user_bp = Blueprint("user", __name__)
schema = UserSchema()

@user_bp.route('/', methods=['POST'])
def create_user():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    if UserModel.exists_by_license(data['license']):
        return jsonify(error_response(409, "User with this license already exists")), 409
    user = UserModel.create(**data)
    return jsonify(created_response("User created successfully", {"user": user})), 201


@user_bp.route('/', methods=['GET'])
def get_users():
    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    users = UserModel.get_all(page=page, limit=limit)
    total = UserModel.collection().count_documents({})
    return jsonify(paginated_response("Users retrieved successfully", "users", users, page, limit, total)), 200

@user_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    user = UserModel.get_by_id(user_id)
    if not user:
        return jsonify(error_response(404, "User not found")), 404
    return jsonify(success_response("User retrieved successfully", {"user": user})), 200


