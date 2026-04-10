from marshmallow import Schema, fields, validate
from app.constants import ROLES


class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(load_default="employee", validate=validate.OneOf(ROLES))

class UserUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=2, max=100))
    role = fields.Str(validate=validate.OneOf(ROLES))
