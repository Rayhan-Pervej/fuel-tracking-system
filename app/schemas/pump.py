from marshmallow import Schema, fields, validate


class PumpSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    location = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    license = fields.Str(required=True, validate=validate.Length(min=3, max=10))


class PumpUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=2, max=100))
    location = fields.Str(validate=validate.Length(min=2, max=200))
    license = fields.Str(validate=validate.Length(min=3, max=10))
