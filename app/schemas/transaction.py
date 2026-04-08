from marshmallow import Schema, fields, validate
from app.constants import FUEL_TYPES


class TransactionSchema(Schema):
    vehicle_id = fields.Str(required=True)
    pump_id = fields.Str(required=True)
    fuel_type = fields.Str(required=True, validate=validate.OneOf(FUEL_TYPES))
    quantity = fields.Decimal(required=True, validate=validate.Range(min=0.1), as_string=False)
