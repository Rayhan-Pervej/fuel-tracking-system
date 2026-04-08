from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from app.models.pump import PumpModel
from app.models.user import UserModel
from app.models.pump_employee import PumpEmployeeModel
from app.schemas.pump_employee import AddPumpEmployeeSchema, UpdatePumpEmployeeRoleSchema
from app.constants import get_cursor_params, success_response, created_response, cursor_response, error_response
from app.middleware.auth import require_auth, require_role

pump_employee_bp = Blueprint("pump_employee", __name__)
add_schema = AddPumpEmployeeSchema()
update_schema = UpdatePumpEmployeeRoleSchema()


@pump_employee_bp.route('/<pump_id>/employees', methods=['POST'])
@require_auth
def add_employee(pump_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    if g.role != "admin" and not PumpEmployeeModel.is_pump_admin(pump_id, g.user_id):
        return jsonify(error_response(403, "You do not have permission")), 403

    try:
        data = add_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400
    
    user = UserModel.get_by_id(data['user_id'])
    if not user:
        return jsonify(error_response(404, "User not found")), 404
    if PumpEmployeeModel.exists(pump_id, data['user_id']):
        return jsonify(error_response(409, "Employee record already exists for this user")), 409
    if user['role'] != 'employee':
        return jsonify(error_response(400, "Only users with employee role can be assigned to a pump")), 400
    
    if data['role'] == 'pump_admin' and PumpEmployeeModel.has_pump_admin(pump_id):
        return jsonify(error_response(400, "Pump already has an admin")), 400
    
    record = PumpEmployeeModel.create(pump_id=pump_id, user_id=data['user_id'], added_by=g.user_id, role=data['role'])
    return jsonify(created_response("Employee added successfully", {"employee": record})), 201


@pump_employee_bp.route('/<pump_id>/employees/<user_id>', methods=['DELETE'])
@require_auth  
def remove_employee(pump_id, user_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    if g.role != "admin" and not PumpEmployeeModel.is_pump_admin(pump_id, g.user_id):
        return jsonify(error_response(403, "You do not have permission")), 403

    if not PumpEmployeeModel.exists(pump_id, user_id):
        return jsonify(error_response(404, "Employee not found for this pump")), 404

    if PumpEmployeeModel.is_pump_admin(pump_id, user_id):
        return jsonify(error_response(400, "Cannot remove the pump admin. Reassign the role first")), 400

    PumpEmployeeModel.remove(pump_id, user_id)
    return jsonify(success_response("Employee removed successfully", {})), 200



@pump_employee_bp.route('/<pump_id>/employees/<user_id>', methods=['PATCH'])
@require_auth
def update_employee_role(pump_id, user_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    if g.role != "admin" and not PumpEmployeeModel.is_pump_admin(pump_id, g.user_id):
        return jsonify(error_response(403, "You do not have permission")), 403
    if not PumpEmployeeModel.exists(pump_id, user_id):
        return jsonify(error_response(404, "Employee not found for this pump")), 404

    try:
        data = update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error_response(400, "Validation failed", errors=e.messages)), 400

    if data['role'] == 'pump_admin' and PumpEmployeeModel.has_pump_admin(pump_id):
        return jsonify(error_response(400, "Pump already has an admin")), 400

    PumpEmployeeModel.update_role(pump_id=pump_id, user_id=user_id, role=data['role'])
    return jsonify(success_response("Employee role updated successfully", {})), 200



@pump_employee_bp.route('/<pump_id>/employees', methods=['GET'])
@require_auth
def get_employees(pump_id):
    pump = PumpModel.get_by_id(pump_id)
    if not pump:
        return jsonify(error_response(404, "Pump not found")), 404
    if g.role != "admin" and not PumpEmployeeModel.exists(pump_id, g.user_id):
        return jsonify(error_response(403, "You can only view employees of pumps you work at")), 403
    
    cursor, limit = get_cursor_params(request)
    if limit is None:
        return jsonify(error_response(400, "Invalid pagination parameters")), 400

    from app.constants import decode_cursor, encode_cursor
    after_dt = decode_cursor(cursor) if cursor else None
    rows = PumpEmployeeModel.get_by_pump(pump_id, after_dt=after_dt, limit=limit)
    has_more = len(rows) > limit
    employees = rows[:limit]
    next_cursor = encode_cursor(employees[-1]["created_at"]) if (has_more and employees) else None
    return jsonify(cursor_response("Employees retrieved successfully", "employees", employees, next_cursor, has_more, limit)), 200

