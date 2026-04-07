from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

mongo = PyMongo()
socketio = SocketIO()
limiter = Limiter(get_remote_address, default_limits=["200 per minute"])