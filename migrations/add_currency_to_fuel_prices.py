"""
Migration description here!
"""
import pymongo

name = 'add_currency_to_fuel_prices'
dependencies = ['add_fuel_type']


def upgrade(db: "pymongo.database.Database"):
    db["fuel_prices"].update_many(
        {"currency": {"$exists": False}},
        {"$set": {"currency": "BDT"}}
    )
    db["transactions"].update_many(
        {},
        {"$unset": {"fuel_type": "", "unit": ""}}
    )


def downgrade(db: "pymongo.database.Database"):
    db["fuel_prices"].update_many({}, {"$unset": {"currency": ""}})
