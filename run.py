from gevent import monkey
monkey.patch_all()

import os
from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, debug=debug, port=port)