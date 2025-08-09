from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["grocery_app"]
collection = db["items"]

# Update quantity of a specific item (e.g., 'lays') to 10
result = collection.update_one(
    {"name": "lays"},
    {"$set": {"quantity": 10}}
)

if result.modified_count:
    print("Stock updated successfully.")
else:
    print("⚠ No matching item found or quantity was already 10.")