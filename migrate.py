import os
import sys
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

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    if command == "upgrade":
        migrate.upgrade()
        print("Upgrade done")
    elif command == "downgrade" and len(sys.argv) > 2:
        migrate.downgrade(sys.argv[2])
        print(f"Downgrade to {sys.argv[2]} done")
    else:
        print("Usage: python migrate.py upgrade | python migrate.py downgrade <migration_name>")
