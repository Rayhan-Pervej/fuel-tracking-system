from marshmallow import Schema, fields, validate


class VehicleSchema(Schema):
    vehicle_number = fields.Str(required=True, validate=validate.Length(min=2, max=10))
   

class VehicleUpdateSchema(Schema):
    vehicle_number = fields.Str(validate=validate.Length(min=2, max=10))

class VehicleFindOrCreateSchema(Schema):
    vehicle_number = fields.Str(required=True, validate=validate.Length(min=2, max=10))
