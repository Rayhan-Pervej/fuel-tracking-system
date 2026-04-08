from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from app.models.vehicle import VehicleModel
from app.models.user import UserModel
from app.schemas.vehicle import VehicleSchema, VehicleUpdateSchema
from app.services.vehicle_service import VehicleService
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response
from app.middleware.auth import require_auth, require_role

vehicle_bp = Blueprint("vehicle", __name__)
schema = VehicleSchema()
update_schema = VehicleUpdateSchema()


@vehicle_bp.route('/', methods=['POST'])
@require_auth
def create_vehicle():
    try:
        data = schema.load(request.get_json() or {})
        
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    
    if g.role != "admin" and g.user_id != data["user_id"]:
        return jsonify(error_response(403, "You can only create vehicles for yourself")), 403

    if not UserModel.get_by_id(data['user_id']):
        return jsonify(error_response(404, "User not found")), 404

    if VehicleModel.exists_by_number(data['vehicle_number']):
        return jsonify(error_response(409, "Vehicle with this number already exists")), 409

    try:
        vehicle = VehicleModel.create(
            user_id=data["user_id"],
            vehicle_number=data["vehicle_number"],
            vehicle_type=data["vehicle_type"])
    except ValueError as e:
        return jsonify(error_response(409, str(e))), 409
    return jsonify(created_response("Vehicle created successfully", {"vehicle": vehicle})), 201

@vehicle_bp.route('/', methods=['GET'])
@require_auth
@require_role("admin")
def get_vehicles():
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    vehicles, next_cursor, has_more = VehicleService.get_filtered(
        user_id=request.args.get("user_id"),
        vehicle_type=request.args.get("type"),
        cursor=cursor, limit=limit, search=request.args.get("search")
    )
    return jsonify(cursor_response("Vehicles retrieved successfully", "vehicles", vehicles, next_cursor, has_more, limit)), 200

@vehicle_bp.route('/user/<user_id>', methods=['GET'])
@require_auth
def get_vehicles_by_user(user_id):
    if not UserModel.get_by_id(user_id):
        return jsonify(error_response(404, "User not found")), 404
    
    if g.role != "admin" and g.user_id != user_id:
        return jsonify(error_response(403, "You can only view your own vehicles")), 403
    
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    vehicles, next_cursor, has_more = VehicleService.get_filtered(
        user_id=user_id, vehicle_type=None,
        cursor=cursor, limit=limit, search=request.args.get("search")
    )
    return jsonify(cursor_response("Vehicles retrieved successfully", "vehicles", vehicles, next_cursor, has_more, limit)), 200

@vehicle_bp.route('/search', methods=['GET'])
@require_auth
@require_role("admin", "employee")
def search_vehicles():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error_response(400, "Query param 'q' is required")), 400
    limit = min(int(request.args.get("limit", 10)), 100)
    vehicles, _, _ = VehicleService.get_filtered(
        user_id=None, vehicle_type=None, cursor=None, limit=limit, search=q
    )
    return jsonify(success_response("Vehicles retrieved successfully", {"vehicles": vehicles})), 200


@vehicle_bp.route('/<vehicle_id>', methods=['GET'])
@require_auth
def get_vehicle(vehicle_id):
    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404
    if g.role != "admin" and g.user_id != vehicle["user_id"]:
        return jsonify(error_response(403, "You can only view your own vehicles")), 403
    return jsonify(success_response("Vehicle retrieved successfully", {"vehicle": vehicle})), 200


@vehicle_bp.route('/<vehicle_id>', methods=['PATCH'])
@require_auth
def update_vehicle(vehicle_id):
    try:
        data = update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if not data:
        return jsonify(error_response(400, "No fields provided to update")), 400

    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404

    if g.role != "admin" and g.user_id != vehicle["user_id"]:
        return jsonify(error_response(403, "You can only update your own vehicles")), 403

    updated = VehicleModel.update(vehicle_id, data)
    return jsonify(success_response("Vehicle updated successfully", {"vehicle": updated})), 200

@vehicle_bp.route('/<vehicle_id>', methods=['DELETE'])
@require_auth
def delete_vehicle(vehicle_id):
    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404
    if g.role != "admin" and g.user_id != vehicle["user_id"]:
        return jsonify(error_response(403, "You can only delete your own vehicles")), 403
    VehicleModel.delete(vehicle_id)
    return jsonify(success_response("Vehicle deleted successfully", {})), 200
