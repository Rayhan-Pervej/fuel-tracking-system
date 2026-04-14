from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from app.constants import FUEL_TYPES


class TransactionSchema(Schema):
    vehicle_number = fields.Str(required=True, validate=validate.Length(min=2, max=10))
    pump_id = fields.Str(required=True)
    fuel_type = fields.Str(required=True, validate=validate.OneOf(FUEL_TYPES))
    quantity = fields.Float(load_default=None, validate=validate.Range(min=0.1))
    total_price = fields.Float(load_default=None, validate=validate.Range(min=0.01))

    @validates_schema
    def validate_quantity_or_price(self, data, **kwargs):
        has_qty = data.get("quantity") is not None
        has_price = data.get("total_price") is not None
        if not has_qty and not has_price:
            raise ValidationError("Provide either quantity or total_price", field_name="_schema")
        if has_qty and has_price:
            raise ValidationError("Provide either quantity or total_price, not both", field_name="_schema")

