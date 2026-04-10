from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.vehicle import VehicleModel
from app.schemas.vehicle import VehicleSchema, VehicleUpdateSchema, VehicleFindOrCreateSchema
from app.services.vehicle_service import VehicleService
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response
from app.middleware.auth import require_auth, require_role

vehicle_bp = Blueprint("vehicle", __name__)
schema = VehicleSchema()
update_schema = VehicleUpdateSchema()
find_or_create_schema = VehicleFindOrCreateSchema()


@vehicle_bp.route('/', methods=['POST'])
@require_auth
def create_vehicle():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if VehicleModel.exists_by_number(data['vehicle_number']):
        return jsonify(error_response(409, "Vehicle with this number already exists")), 409

    try:
        vehicle = VehicleModel.create(vehicle_number=data["vehicle_number"])
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
        cursor=None, limit=limit, search=q
    )
    return jsonify(success_response("Vehicles retrieved successfully", {"vehicles": vehicles})), 200


@vehicle_bp.route('/find-or-create', methods=['POST'])
@require_auth
def find_or_create_vehicle():
    try:
        data = find_or_create_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    vehicle = VehicleModel.find_by_number(data["vehicle_number"])
    if vehicle:
        return jsonify(success_response("Vehicle found", {"vehicle": vehicle, "created": False})), 200

    try:
        vehicle = VehicleModel.create(vehicle_number=data["vehicle_number"])
    except ValueError as e:
        return jsonify(error_response(409, str(e))), 409
    return jsonify(created_response("Vehicle created", {"vehicle": vehicle, "created": True})), 201


@vehicle_bp.route('/<vehicle_id>', methods=['GET'])
@require_auth
def get_vehicle(vehicle_id):
    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404
    return jsonify(success_response("Vehicle retrieved successfully", {"vehicle": vehicle})), 200


@vehicle_bp.route('/<vehicle_id>', methods=['PATCH'])
@require_auth
@require_role("admin")
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

    updated = VehicleModel.update(vehicle_id, data)
    return jsonify(success_response("Vehicle updated successfully", {"vehicle": updated})), 200


@vehicle_bp.route('/<vehicle_id>', methods=['DELETE'])
@require_auth
@require_role("admin")
def delete_vehicle(vehicle_id):
    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404
    VehicleModel.delete(vehicle_id)
    return jsonify(success_response("Vehicle deleted successfully", {})), 200
