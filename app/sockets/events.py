import logging
import time
from app.extensions import mongo, socketio

logger = logging.getLogger(__name__)


def watch_transactions():
    while True:
        try:
            with mongo.db["transactions"].watch() as stream:
                for change in stream:
                    if change["operationType"] == "insert":
                        doc = change["fullDocument"]
                        socketio.emit("new_transaction", doc, namespace="/dashboard")

        except Exception as e:
            logger.error(f"Change Stream Error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)



def register_socket_events():
    socketio.start_background_task(watch_transactions)
