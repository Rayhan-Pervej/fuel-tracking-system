from marshmallow import Schema, fields, validate


class VehicleSchema(Schema):
    user_id = fields.Str(required=True)
    vehicle_number = fields.Str(required=True, validate=validate.Length(min=2, max=10))
    type = fields.Str(required=True, validate=validate.OneOf(["car", "truck", "bike", "bus"]))
