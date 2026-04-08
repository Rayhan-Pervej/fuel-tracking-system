from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.vehicle import VehicleModel
from app.models.user import UserModel
from app.schemas.vehicle import VehicleSchema
from app.constants import get_pagination_params, success_response, created_response, paginated_response, error_response
from app.middleware.auth import require_auth, require_role

vehicle_bp = Blueprint("vehicle", __name__)
schema = VehicleSchema()


@vehicle_bp.route('/', methods=['POST'])
@require_auth
def create_vehicle():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if not UserModel.get_by_id(data['user_id']):
        return jsonify(error_response(404, "User not found")), 404

    if VehicleModel.exists_by_number(data['vehicle_number']):
        return jsonify(error_response(409, "Vehicle with this number already exists")), 409

    vehicle = VehicleModel.create(
        user_id=data["user_id"],
        vehicle_number=data["vehicle_number"],
        vehicle_type=data["vehicle_type"])
    return jsonify(created_response("Vehicle created successfully", {"vehicle": vehicle})), 201

@vehicle_bp.route('/', methods=['GET'])
@require_auth
@require_role("admin")
def get_vehicles():
    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    vehicles = VehicleModel.get_all(page=page, limit=limit)
    total = VehicleModel.collection().count_documents({})
    return jsonify(paginated_response("Vehicles retrieved successfully", "vehicles", vehicles, page, limit, total)), 200

@vehicle_bp.route('/user/<user_id>', methods=['GET'])
@require_auth
def get_vehicles_by_user(user_id):
    if not UserModel.get_by_id(user_id):
        return jsonify(error_response(404, "User not found")), 404

    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    vehicles = VehicleModel.get_by_user_id(user_id, page=page, limit=limit)
    total = VehicleModel.collection().count_documents({"user_id": user_id})
    return jsonify(paginated_response("Vehicles retrieved successfully", "vehicles", vehicles, page, limit, total)), 200

@vehicle_bp.route('/<vehicle_id>', methods=['GET'])
@require_auth
def get_vehicle(vehicle_id):
    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404
    return jsonify(success_response("Vehicle retrieved successfully", {"vehicle": vehicle})), 200
