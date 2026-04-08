name = 'add_fuel_price_unique_index'
dependencies = ['add_auth_fields_to_users']

def upgrade(db):
    db["fuel_prices"].create_index(
        [("fuel_type", 1), ("effective_from", 1)],
        unique=True,
        name="fuel_type_effective_from_unique"
    )

def downgrade(db):
    db["fuel_prices"].drop_index("fuel_type_effective_from_unique")
