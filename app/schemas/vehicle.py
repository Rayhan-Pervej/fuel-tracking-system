from marshmallow import Schema, fields, validate


class VehicleSchema(Schema):
    user_id = fields.Str(required=True)
    vehicle_number = fields.Str(required=True, validate=validate.Length(min=2, max=10))
    vehicle_type = fields.Str(required=True, validate=validate.OneOf(["car", "truck", "bike", "bus"]))

class VehicleUpdateSchema(Schema):
    vehicle_number = fields.Str(validate=validate.Length(min=2, max=10))
    vehicle_type = fields.Str(validate=validate.OneOf(["car", "truck", "bike", "bus"]))
