from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.fuel_price import FuelPriceModel
from app.schemas.fuel_price import FuelPriceSchema
from app.constants import get_pagination_params, success_response, created_response, paginated_response, error_response

fuel_price_bp = Blueprint("fuel_price", __name__)
schema = FuelPriceSchema()

@fuel_price_bp.route('/', methods=['POST'])
def create_fuel_price():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    fuel_price = FuelPriceModel.create(**data)
    return jsonify(created_response("Fuel price created successfully", {"fuel_price": fuel_price})), 201


@fuel_price_bp.route('/latest/<fuel_type>', methods=['GET'])
def get_latest_fuel_price(fuel_type):
    fuel_price = FuelPriceModel.get_latest(fuel_type)
    if not fuel_price:
        return jsonify(error_response(404, "No fuel price found")), 404
    return jsonify(success_response("Fuel price retrieved successfully", {"fuel_price": fuel_price})), 200


@fuel_price_bp.route('/', methods=['GET'])
def get_fuel_prices():
    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    fuel_prices = FuelPriceModel.get_all(page=page, limit=limit)
    total = FuelPriceModel.collection().count_documents({})
    return jsonify(paginated_response("Fuel prices retrieved successfully", "fuel_prices", fuel_prices, page, limit, total)), 200


@fuel_price_bp.route('/<fuel_price_id>', methods=['GET'])
def get_fuel_price(fuel_price_id):
    fuel_price = FuelPriceModel.get_by_id(fuel_price_id)
    if not fuel_price:
        return jsonify(error_response(404, "Fuel price not found")), 404
    return jsonify(success_response("Fuel price retrieved successfully", {"fuel_price": fuel_price})), 200
