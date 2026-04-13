import logging
import time
from app.extensions import mongo, socketio
from flask import current_app, request
import jwt
from flask_socketio import emit, disconnect, join_room
from app.models.pump_employee import PumpEmployeeModel
from app.constants import FUEL_TYPES

logger = logging.getLogger(__name__)
CLIENT_SCOPE = {}

def get_dashboard_scope(user_id, role):
    if role == "admin":
        return {"room": "dashboard_admin", "pump_id": None}
    assignment = PumpEmployeeModel.get_by_user(user_id)
    if assignment and assignment.get("role") == "pump_admin":
        return {"room": f"pump:{assignment['pump_id']}", "pump_id": assignment["pump_id"]}
    return None


def get_fuel_type_totals(pump_id=None):
    pipeline = []
    if pump_id is not None:
        pipeline.append({"$match": {"pump_id": pump_id}})

    pipeline.extend([
        {
            "$lookup": {
                "from": "fuel_prices",
                "localField": "fuel_price_id",
                "foreignField": "_id",
                "as": "fuel_price"
            }
        },
        {"$unwind": "$fuel_price"},
        {
            "$group": {
                "_id": "$fuel_price.fuel_type",
                "total_quantity": {"$sum": "$quantity"}
            }
        }
    ])

    rows = list(mongo.db["transactions"].aggregate(pipeline))
    totals = {fuel_type: 0.0 for fuel_type in FUEL_TYPES}
    for row in rows:
        fuel_type = row.get("_id")
        if fuel_type in totals:
            totals[fuel_type] = round(row.get("total_quantity", 0.0), 2)
    return totals


def get_dashboard_stats(pump_id=None):
    pipeline = []

    if pump_id is not None:
        pipeline.append({"$match": {"pump_id": pump_id}})

    pipeline.append({
        "$group": {
            "_id": None,
            "total_transactions": {"$sum": 1},
            "total_revenue": {"$sum": "$total_price"},
            "total_fuel_dispensed": {"$sum": "$quantity"}
        }
    })
    result = list(mongo.db["transactions"].aggregate(pipeline))
    if not result:
        return {
            "total_transactions": 0,
            "total_revenue": 0.0,
            "total_fuel_dispensed": 0.0,
            "fuel_type_totals": get_fuel_type_totals(pump_id)
        }
    row = result[0]
    return {
        "total_transactions": row["total_transactions"],
        "total_revenue": round(row["total_revenue"], 2),
        "total_fuel_dispensed": round(row["total_fuel_dispensed"], 2),
        "fuel_type_totals": get_fuel_type_totals(pump_id)
    }


def watch_transactions():
    while True:
        try:
            with mongo.db["transactions"].watch() as stream:
                for change in stream:
                    if change["operationType"] == "insert":
                        doc = change["fullDocument"]
                        doc = enrich_transactions([doc])[0]
                        pump_id = doc["pump_id"]

                        socketio.emit(
                                "new_transaction",
                                {"transaction": doc, "stats": get_dashboard_stats()},
                                namespace="/dashboard",
                                room="dashboard_admin"
                        )

                        socketio.emit(
                                "new_transaction",
                                {"transaction": doc, "stats": get_dashboard_stats(pump_id)},
                                namespace="/dashboard",
                                room=f"pump:{pump_id}"
                        )

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

def build_init_payload(pump_id=None):
    stats = get_dashboard_stats(pump_id)
    query = {"pump_id": pump_id} if pump_id else {}
    recent = list(mongo.db["transactions"].find(query).sort("created_at", -1).limit(20))
    recent = enrich_transactions(recent)
    return {"stats": stats, "transactions": recent}

@socketio.on("connect", namespace="/dashboard")
def on_connect(auth=None):
    token = (auth or {}).get("token", "")
    if not token:
        disconnect()
        return
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.InvalidTokenError:
        disconnect()
        return

    role = payload.get("role")
    user_id = payload.get("user_id")
    if not user_id:
        disconnect()
        return

    scope = get_dashboard_scope(user_id, role)
    if not scope:
        disconnect()
        return

    CLIENT_SCOPE[request.sid] = scope
    join_room(scope["room"])
    logger.info("Dashboard client connected")
    init_payload = build_init_payload(pump_id=scope["pump_id"])
    emit("init", init_payload)

@socketio.on("disconnect", namespace="/dashboard")
def on_disconnect():
    CLIENT_SCOPE.pop(request.sid, None)


@socketio.on("request_init", namespace="/dashboard")
def handle_request_init():
    scope = CLIENT_SCOPE.get(request.sid)
    if not scope:
        disconnect()
        return
    payload = build_init_payload(pump_id=scope["pump_id"])
    emit("init", payload)

def register_socket_events():
    socketio.start_background_task(watch_transactions)

