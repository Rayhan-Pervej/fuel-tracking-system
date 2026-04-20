from gevent import monkey
monkey.patch_all()

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=app.config["DEBUG"], port=app.config["PORT"])
