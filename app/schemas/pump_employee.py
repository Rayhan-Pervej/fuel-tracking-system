from marshmallow import Schema, fields, validate
from app.constants import PUMP_EMPLOYEE_ROLES


class AddPumpEmployeeSchema(Schema):
    email = fields.Email(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(PUMP_EMPLOYEE_ROLES))


class UpdatePumpEmployeeRoleSchema(Schema):
    role = fields.Str(required=True, validate=validate.OneOf(PUMP_EMPLOYEE_ROLES))
