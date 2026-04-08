import logging
import time
from flask_socketio import emit, disconnect
from app.extensions import mongo, socketio
from flask import current_app
import jwt
logger = logging.getLogger(__name__)


def get_dashboard_stats():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_transactions": {"$sum": 1},
                "total_revenue": {"$sum": "$total_price"},
                "total_fuel_dispensed": {"$sum": "$quantity"}
            }
        }
    ]
    result = list(mongo.db["transactions"].aggregate(pipeline))
    if not result:
        return {"total_transactions": 0, "total_revenue": 0.0, "total_fuel_dispensed": 0.0}
    row = result[0]
    return {
        "total_transactions": row["total_transactions"],
        "total_revenue": round(row["total_revenue"], 2),
        "total_fuel_dispensed": round(row["total_fuel_dispensed"], 2)
    }


def watch_transactions():
    while True:
        try:
            with mongo.db["transactions"].watch() as stream:
                for change in stream:
                    if change["operationType"] == "insert":
                        doc = change["fullDocument"]
                        doc = enrich_transactions([doc])[0]
                        stats = get_dashboard_stats()
                        socketio.emit("new_transaction", {
                            "transaction": doc,
                            "stats": stats
                        }, namespace="/dashboard")

        except Exception as e:
            logger.error(f"Change Stream Error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)


def enrich_transactions(transactions):
    for txn in transactions:
        txn["created_at"] = txn["created_at"].isoformat() if hasattr(txn["created_at"], "isoformat") else str(txn["created_at"])
        fp = mongo.db["fuel_prices"].find_one({"_id": txn["fuel_price_id"]}, {"fuel_type": 1, "unit": 1, "currency": 1})
        if fp:
            txn["fuel_type"] = fp["fuel_type"]
            txn["unit"] = fp["unit"]
            txn["currency"] = fp["currency"]
        
        vehicle = mongo.db["vehicles"].find_one({"_id": txn["vehicle_id"]}, {"vehicle_number": 1})
        txn["vehicle_number"] = vehicle["vehicle_number"] if vehicle else txn["vehicle_id"]
        pump = mongo.db["pumps"].find_one({"_id": txn["pump_id"]}, {"name": 1})
        txn["pump_name"] = pump["name"] if pump else txn["pump_id"]

    return transactions


@socketio.on("connect", namespace="/dashboard")
def on_connect(auth=None):
    token = (auth or {}).get("token", "")
    if not token:
        disconnect()
        return
    try:
        jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.InvalidTokenError:
        disconnect()
        return

    logger.info("Dashboard client connected")
    stats = get_dashboard_stats()
    recent = list(mongo.db["transactions"].find().sort("created_at", -1).limit(20))
    recent = enrich_transactions(recent)
    emit("init", {"stats": stats, "transactions": recent})


def register_socket_events():
    socketio.start_background_task(watch_transactions)

    