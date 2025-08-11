from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.environ.get("MONGO_DB_NAME", "grocery_app")]
collection = db["items"]

# Update stock of a specific item (e.g., 'lays') to 10
result = collection.update_one(
    {"name": "lays"},
    {"$set": {"stock": 10}}
)

if result.modified_count:
    print("Stock updated successfully.")
else:
    print("⚠ No matching item found or stock was already 10.")