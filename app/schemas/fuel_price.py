from marshmallow import Schema, fields, validate
from app.constants import FUEL_TYPES


class FuelPriceSchema(Schema):
    fuel_type = fields.Str(required=True, validate=validate.OneOf(FUEL_TYPES))
    price_per_unit = fields.Float(required=True, validate=validate.Range(min=0.1))
    unit = fields.Str(required=True, validate=validate.OneOf(["liter", "gallon"]))
    effective_from = fields.Str(required=True, validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}$', error="Date must be in YYYY-MM-DD format"))
