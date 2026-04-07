import os
import pymongo
from dotenv import load_dotenv
from pymongo_migrate.mongo_migrate import MongoMigrate

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
client = pymongo.MongoClient(mongo_uri)
db_name = pymongo.uri_parser.parse_uri(mongo_uri)["database"]

migrate = MongoMigrate(
    client=client,
    database=db_name,
    migrations_dir="./migrations"
)
