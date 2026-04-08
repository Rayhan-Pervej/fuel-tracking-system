from marshmallow import Schema, fields, validate
from app.constants import ROLES


class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(load_default="customer", validate=validate.OneOf(ROLES))
    license = fields.Str(required=True, validate=validate.Length(min=3, max=10))

