from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

mongo = PyMongo()
from pymongo import MongoClient
# mongo_client is initialized in create_app after mongo.init_app()
mongo_client: MongoClient = None
socketio = SocketIO()
limiter = Limiter(get_remote_address, default_limits=["200 per minute"])