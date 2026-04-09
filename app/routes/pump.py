from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from app.middleware.auth import require_auth, require_role
from app.models.pump import PumpModel
from app.schemas.pump import PumpSchema, PumpUpdateSchema
from app.services.pump_service import PumpService
from app.models.pump_employee import PumpEmployeeModel
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response

pump_bp = Blueprint("pump", __name__)
schema = PumpSchema()
update_schema = PumpUpdateSchema()


@pump_bp.route('/', methods=['POST'])
@require_auth
@require_role("admin")
def create_pump():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if PumpModel.exists_by_license(data['license']):
        return jsonify(error_response(409, "Pump with this license already exists")), 409

    try:
        pump = PumpModel.create(**data)
    except ValueError as e:
        return jsonify(error_response(409, str(e))), 409
    return jsonify(created_response("Pump created successfully", {"pump": pump})), 201


@pump_bp.route('/', methods=['GET'])
@require_auth
def get_pumps():
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    pumps, next_cursor, has_more = PumpService.get_filtered(
        location=request.args.get("location"),
        license=request.args.get("license"),
        cursor=cursor,
        limit=limit
    )
    return jsonify(cursor_response("Pumps retrieved successfully", "pumps", pumps, next_cursor, has_more, limit)), 200


@pump_bp.route('/<pump_id>', methods=['GET'])
@require_auth
def get_pump(pump_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    return jsonify(success_response("Pump retrieved successfully", {"pump": pump})), 200


@pump_bp.route('/<pump_id>', methods=['PATCH'])
@require_auth
@require_role("admin")
def update_pump(pump_id):
    try:
        data = update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if not data:
        return jsonify(error_response(400, "No fields provided to update")), 400

    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404

    if "license" in data and data["license"] != pump["license"]:
        if PumpModel.exists_by_license(data["license"]):
            return jsonify(error_response(409, "Pump with this license already exists")), 409

    updated = PumpModel.update(pump_id, data)
    return jsonify(success_response("Pump updated successfully", {"pump": updated})), 200

@pump_bp.route('/<pump_id>', methods=['DELETE'])
@require_auth
@require_role("admin")
def delete_pump(pump_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    PumpEmployeeModel.remove_by_pump(pump_id)
    PumpModel.delete(pump_id)
    return jsonify(success_response("Pump deleted successfully", {})), 200
