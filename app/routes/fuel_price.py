from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.fuel_price import FuelPriceModel
from app.schemas.fuel_price import FuelPriceSchema
from app.services.fuel_price_service import FuelPriceService
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response
from app.middleware.auth import require_auth, require_role

fuel_price_bp = Blueprint("fuel_price", __name__)
schema = FuelPriceSchema()

@fuel_price_bp.route('/', methods=['POST'])
@require_auth
@require_role("admin")
def create_fuel_price():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    fuel_price = FuelPriceModel.create(**data)
    return jsonify(created_response("Fuel price created successfully", {"fuel_price": fuel_price})), 201


@fuel_price_bp.route('/latest/<fuel_type>', methods=['GET'])
@require_auth
def get_latest_fuel_price(fuel_type):
    fuel_price = FuelPriceModel.get_latest(fuel_type)
    if not fuel_price:
        return jsonify(error_response(404, "No fuel price found")), 404
    return jsonify(success_response("Fuel price retrieved successfully", {"fuel_price": fuel_price})), 200


@fuel_price_bp.route('/', methods=['GET'])
@require_auth
def get_fuel_prices():
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    fuel_prices, next_cursor, has_more = FuelPriceService.get_filtered(
        fuel_type=request.args.get("fuel_type"),
        effective_from=request.args.get("effective_from"),
        effective_from_after=request.args.get("effective_from_after"),
        effective_from_before=request.args.get("effective_from_before"),
        cursor=cursor, limit=limit
    )
    return jsonify(cursor_response("Fuel prices retrieved successfully", "fuel_prices", fuel_prices, next_cursor, has_more, limit)), 200


@fuel_price_bp.route('/<fuel_price_id>', methods=['GET'])
@require_auth
def get_fuel_price(fuel_price_id):
    fuel_price = FuelPriceModel.get_by_id(fuel_price_id)
    if not fuel_price:
        return jsonify(error_response(404, "Fuel price not found")), 404
    return jsonify(success_response("Fuel price retrieved successfully", {"fuel_price": fuel_price})), 200
