import os
from dotenv import load_dotenv
from pymongo_migrate.mongo_migrate import MongoMigrate

load_dotenv()

migrate = MongoMigrate(
    mongo_url=os.getenv("MONGO_URI"),
    migrations_path="./migrations"
)
