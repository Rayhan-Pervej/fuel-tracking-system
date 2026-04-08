from marshmallow import Schema, fields, validate, ValidationError as MarshmallowError
from app.constants import FUEL_TYPES, CURRENCIES, UNITS
from datetime import datetime


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise MarshmallowError("Date must be a valid date in YYYY-MM-DD format")


class FuelPriceSchema(Schema):
    fuel_type = fields.Str(required=True, validate=validate.OneOf(FUEL_TYPES))
    price_per_unit = fields.Float(required=True, validate=validate.Range(min=0.1))
    unit = fields.Str(required=True, validate=validate.OneOf(UNITS))
    currency = fields.Str(load_default="BDT", validate=validate.OneOf(CURRENCIES))
    effective_from = fields.Str(required=True, validate=validate_date)
