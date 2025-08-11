from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.environ.get("MONGO_DB_NAME", "grocery_app")]
collection = db["items"]

item = collection.find_one({"name": "lays"})
print(item)