from marshmallow import Schema, fields, validate
from app.constants import PUMP_EMPLOYEE_ROLES


class AddPumpEmployeeSchema(Schema):
    mode = fields.Str(required=True, validate=validate.OneOf(["existing", "new"]))
    email = fields.Email(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(PUMP_EMPLOYEE_ROLES))
    name = fields.Str(validate=validate.Length(min=2, max=100))
    password = fields.Str(validate=validate.Length(min=8))

class UpdatePumpEmployeeRoleSchema(Schema):
    role = fields.Str(required=True, validate=validate.OneOf(PUMP_EMPLOYEE_ROLES))
