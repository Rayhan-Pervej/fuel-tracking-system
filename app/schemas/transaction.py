from marshmallow import Schema, fields, validate
from app.constants import FUEL_TYPES


class TransactionSchema(Schema):
    vehicle_id = fields.Str(required=True)
    pump_id = fields.Str(required=True)
    fuel_type = fields.Str(required=True, validate=validate.OneOf(FUEL_TYPES))
    quantity = fields.Float(required=True, validate=validate.Range(min=0.1))
    total_price = fields.Float(load_default=None, validate=validate.Range(min=0.01))

