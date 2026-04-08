import pymongo

name = 'add_auth_fields_to_users'
dependencies = ['add_currency_to_fuel_prices']


def upgrade(db: "pymongo.database.Database"):
    # Add email, password_hash, role to existing users that don't have them
    db["users"].update_many(
        {"email": {"$exists": False}},
        {"$set": {"email": None, "password_hash": None, "role": "customer"}}
    )


def downgrade(db: "pymongo.database.Database"):
    db["users"].update_many(
        {},
        {"$unset": {"email": "", "password_hash": "", "role": ""}}
    )
