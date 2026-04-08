from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.middleware.auth import require_auth, require_role
from app.models.pump import PumpModel
from app.schemas.pump import PumpSchema
from app.constants import get_pagination_params, success_response, created_response, paginated_response, error_response

pump_bp = Blueprint("pump", __name__)
schema = PumpSchema()


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

    pump = PumpModel.create(**data)
    return jsonify(created_response("Pump created successfully", {"pump": pump})), 201


@pump_bp.route('/', methods=['GET'])
@require_auth
def get_pumps():
    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    pumps = PumpModel.get_all(page=page, limit=limit)
    total = PumpModel.collection().count_documents({})
    return jsonify(paginated_response("Pumps retrieved successfully", "pumps", pumps, page, limit, total)), 200


@pump_bp.route('/<pump_id>', methods=['GET'])
@require_auth
def get_pump(pump_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    return jsonify(success_response("Pump retrieved successfully", {"pump": pump})), 200

