"""
Migration description here!
"""
import pymongo

name = 'add_fuel_type'
dependencies = []


def upgrade(db: "pymongo.database.Database"):
    db["fuel_prices"].update_many(
        {"fuel_type": {"$exists": False}},
        {"$set": {"fuel_type": "octane"}}
    )
    db["transactions"].update_many(
        {"fuel_type": {"$exists": False}},
        {"$set": {"fuel_type": "octane"}}
    )



def downgrade(db: "pymongo.database.Database"):
    db["fuel_prices"].update_many({}, {"$unset": {"fuel_type": ""}})
    db["transactions"].update_many({}, {"$unset": {"fuel_type": ""}})

