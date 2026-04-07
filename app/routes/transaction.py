from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models.transaction import TransactionModel
from app.models.vehicle import VehicleModel
from app.models.pump import PumpModel
from app.models.fuel_price import FuelPriceModel
from app.schemas.transaction import TransactionSchema
from app.constants import get_pagination_params, success_response, created_response, paginated_response, error_response

transaction_bp = Blueprint("transaction", __name__)
schema = TransactionSchema()


@transaction_bp.route('/', methods=['POST'])
def create_transaction():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if not VehicleModel.get_by_id(data['vehicle_id']):
        return jsonify(error_response(404, "Vehicle not found")), 404

    if not PumpModel.get_by_id(data['pump_id']):
        return jsonify(error_response(404, "Pump not found")), 404

    fuel_price = FuelPriceModel.get_latest(data["fuel_type"])
    if not fuel_price:
        return jsonify(error_response(404, f"No active price found for {data['fuel_type']}")), 404

    total_price = data['quantity'] * fuel_price['price_per_unit']

    transaction = TransactionModel.create(
        vehicle_id=data["vehicle_id"],
        pump_id=data["pump_id"],
        fuel_price_id=fuel_price["_id"],
        quantity=data["quantity"],
        total_price=round(total_price, 2)
    )

    return jsonify(created_response("Transaction created successfully", {"transaction": transaction})), 201


@transaction_bp.route('/', methods=['GET'])
def get_transactions():
    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    transactions = TransactionModel.get_all(page=page, limit=limit)
    total = TransactionModel.collection().count_documents({})
    return jsonify(paginated_response("Transactions retrieved successfully", "transactions", transactions, page, limit, total)), 200

@transaction_bp.route('/vehicle/<vehicle_id>', methods=['GET'])
def get_transactions_by_vehicle(vehicle_id):
    if not VehicleModel.get_by_id(vehicle_id):
        return jsonify(error_response(404, "Vehicle not found")), 404

    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    transactions = TransactionModel.get_by_vehicle(vehicle_id, page=page, limit=limit)
    total = TransactionModel.collection().count_documents({"vehicle_id": vehicle_id})
    return jsonify(paginated_response("Transactions retrieved successfully", "transactions", transactions, page, limit, total)), 200

@transaction_bp.route('/pump/<pump_id>', methods=['GET'])
def get_transactions_by_pump(pump_id):
    if not PumpModel.get_by_id(pump_id):
        return jsonify(error_response(404, "Pump not found")), 404

    page, limit = get_pagination_params(request)
    if page is None or limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400
    transactions = TransactionModel.get_by_pump(pump_id, page=page, limit=limit)
    total = TransactionModel.collection().count_documents({"pump_id": pump_id})
    return jsonify(paginated_response("Transactions retrieved successfully", "transactions", transactions, page, limit, total)), 200

@transaction_bp.route('/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    transaction = TransactionModel.get_by_id(transaction_id)
    if not transaction:
        return jsonify(error_response(404, "Transaction not found")), 404
    return jsonify(success_response("Transaction retrieved successfully", {"transaction": transaction})), 200

