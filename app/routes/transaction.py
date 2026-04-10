from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from app.models.transaction import TransactionModel
from app.models.vehicle import VehicleModel
from app.models.pump import PumpModel
from app.models.fuel_price import FuelPriceModel
from app.schemas.transaction import TransactionSchema
from app.services.transaction_service import TransactionService
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response
from app.middleware.auth import require_auth, require_role
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from app.extensions import mongo_client
from app.models.pump_employee import PumpEmployeeModel

transaction_bp = Blueprint("transaction", __name__)
schema = TransactionSchema()

DATE_MIN = "2000-01-01"


def _resolve_date_range(from_date, to_date):
    """
    Apply frontend defaulting rules and validate format.
    Returns (from_date, to_date, error_response_or_None).
    """
    if not from_date and not to_date:
        return None, None, None

    if from_date and not to_date:
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    elif to_date and not from_date:
        from_date = DATE_MIN

    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return None, None, "Dates must be in YYYY-MM-DD format"

    return from_date, to_date, None


@transaction_bp.route('/', methods=['POST'])
@require_auth
@require_role("admin", "employee")
def create_transaction():
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    vehicle = VehicleModel.find_by_number(data["vehicle_number"])
    if not vehicle:
        vehicle = VehicleModel.create(vehicle_number=data["vehicle_number"])

    if not PumpModel.get_by_id(data['pump_id']):
        return jsonify(error_response(404, "Pump not found")), 404

    if g.role != "admin" and not PumpEmployeeModel.exists(data['pump_id'], g.user_id):
        return jsonify(error_response(403, "You are not assigned to this pump")), 403

    # transaction control logic is moved to service layer to ensure atomicity with MongoDB transactions
    with mongo_client.start_session() as session:
        with session.start_transaction():
            fuel_price = FuelPriceModel.get_latest(data["fuel_type"], session=session)
            if not fuel_price:
                return jsonify(error_response(404, f"No active price found for {data['fuel_type']}")), 404
            total_price = float(
                (Decimal(str(data['quantity'])) * Decimal(str(fuel_price['price_per_unit'])))
                .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
            if data.get("total_price") is not None:
                submitted = round(data["total_price"], 2)
                if submitted != total_price:
                    return jsonify(error_response(400, f"total_price mismatch: expected {total_price}, got {submitted}")), 400
            
            transaction = TransactionModel.create(
                vehicle_id=vehicle["_id"],
                pump_id=data["pump_id"],
                fuel_price_id=fuel_price["_id"],
                quantity=data["quantity"],
                total_price=total_price,
                session=session
            )

    return jsonify(created_response("Transaction created successfully", {"transaction": transaction})), 201


@transaction_bp.route('/', methods=['GET'])
@require_auth
@require_role("admin")
def get_transactions():
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400

    from_date, to_date, err = _resolve_date_range(request.args.get("from"), request.args.get("to"))
    if err:
        return jsonify(error_response(400, err)), 400

    transactions, next_cursor, has_more = TransactionService.get_filtered(
        from_date=from_date,
        to_date=to_date,
        vehicle_number=request.args.get("vehicle_number"),
        pump_name=request.args.get("pump_name"),
        pump_license=request.args.get("pump_license"),
        fuel_type=request.args.get("fuel_type"),
        cursor=cursor,
        limit=limit
    )

    return jsonify(cursor_response("Transactions retrieved successfully", "transactions", transactions, next_cursor, has_more, limit)), 200


@transaction_bp.route('/vehicle/<vehicle_id>', methods=['GET'])
@require_auth
def get_transactions_by_vehicle(vehicle_id):
    vehicle = VehicleModel.get_by_id(vehicle_id)
    if not vehicle:
        return jsonify(error_response(404, "Vehicle not found")), 404

    from_date, to_date, err = _resolve_date_range(request.args.get("from"), request.args.get("to"))
    if err:
        return jsonify(error_response(400, err)), 400

    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400

    transactions, next_cursor, has_more = TransactionService.get_filtered(
        from_date=from_date, to_date=to_date,
        vehicle_id=vehicle_id, pump_id=None,
        fuel_type=request.args.get("fuel_type"),
        cursor=cursor, limit=limit
    )
    return jsonify(cursor_response("Transactions retrieved successfully", "transactions", transactions, next_cursor, has_more, limit)), 200


@transaction_bp.route('/pump/<pump_id>', methods=['GET'])
@require_auth
def get_transactions_by_pump(pump_id):
    if not PumpModel.get_by_id(pump_id):
        return jsonify(error_response(404, "Pump not found")), 404
    if g.role != "admin" and not PumpEmployeeModel.is_pump_admin(pump_id, g.user_id):
        if not PumpEmployeeModel.exists(pump_id, g.user_id):
            return jsonify(error_response(403, "You can only view transactions for pumps you work at")), 403
    from_date, to_date, err = _resolve_date_range(request.args.get("from"), request.args.get("to"))
    if err:
        return jsonify(error_response(400, err)), 400

    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400

    transactions, next_cursor, has_more = TransactionService.get_filtered(
        from_date=from_date, to_date=to_date,
        vehicle_id=None, pump_id=pump_id,
        fuel_type=request.args.get("fuel_type"),
        cursor=cursor, limit=limit
    )
    return jsonify(cursor_response("Transactions retrieved successfully", "transactions", transactions, next_cursor, has_more, limit)), 200


@transaction_bp.route('/<transaction_id>', methods=['GET'])
@require_auth
def get_transaction(transaction_id):
    transaction = TransactionModel.get_by_id(transaction_id)
    if not transaction:
        return jsonify(error_response(404, "Transaction not found")), 404
    if g.role != "admin":
        if not PumpEmployeeModel.exists(transaction["pump_id"], g.user_id):
            return jsonify(error_response(403, "You do not have permission to view this transaction")), 403
    TransactionService.enrich([transaction])
    return jsonify(success_response("Transaction retrieved successfully", {"transaction": transaction})), 200
