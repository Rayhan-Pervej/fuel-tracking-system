import logging
from flask import Flask, render_template
from flask_cors import CORS
from app import extensions
from app.config import Config, validate_config
from app.extensions import mongo, socketio, limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def _create_indexes():
    mongo.db["transactions"].create_index("vehicle_id")
    mongo.db["transactions"].create_index("pump_id")
    mongo.db["transactions"].create_index("created_at")
    mongo.db["vehicles"].create_index("user_id")
    mongo.db["fuel_prices"].create_index("fuel_type")
    mongo.db["users"].create_index("email", unique=True, sparse=True)
    mongo.db["vehicles"].create_index("vehicle_number", unique=True)
    mongo.db["pumps"].create_index("license", unique=True)
    mongo.db["pump_employees"].create_index("pump_id")
    mongo.db["pump_employees"].create_index([("pump_id", 1), ("user_id", 1)], unique=True)


def create_app():
    validate_config()
    app = Flask(__name__)
    CORS(app)
    limiter.init_app(app)
    app.config.from_object(Config)
    mongo.init_app(app)
    extensions.mongo_client = mongo.cx  # mongo.cx is the underlying MongoClient
    socketio.init_app(app, cors_allowed_origins="*", async_mode="gevent")
    from app.sockets.events import register_socket_events
    register_socket_events()
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.vehicle import vehicle_bp
    from app.routes.pump import pump_bp
    from app.routes.transaction import transaction_bp
    from app.routes.fuel_price import fuel_price_bp
    from app.routes.pump_employee import pump_employee_bp


    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(vehicle_bp, url_prefix="/api/vehicles")
    app.register_blueprint(pump_bp, url_prefix="/api/pumps")
    app.register_blueprint(transaction_bp, url_prefix="/api/transactions")
    app.register_blueprint(fuel_price_bp, url_prefix="/api/fuel-prices")
    app.register_blueprint(pump_employee_bp, url_prefix="/api/pumps")


    with app.app_context():
        _create_indexes()

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")
    return app