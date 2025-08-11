from pymongo import MongoClient
import os

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://akashkkota:UTr1O4G1UMXq60pB@cluster0.g4cygtk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
)
DB_NAME = os.environ.get("MONGO_DB_NAME", "grocery_app")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
items = db["items"]

docs = [
    {"name": "Apple", "price": 50, "description": "Fresh red apples", "stock": 100, "category": "fruits", "offer": "", "image": "apple.jpg"},
    {"name": "Chips", "price": 30, "description": "Salted chips", "stock": 200, "category": "snacks", "offer": "", "image": "chips.jpg"},
    {"name": "Juice", "price": 25, "description": "Mango juice", "stock": 150, "category": "beverages", "offer": "", "image": "juice.jpg"},
]

# Idempotent insert: don't duplicate by name
for d in docs:
    existing = items.find_one({"name": d["name"]})
    if not existing:
        items.insert_one(d)

print("Seeded items count:", items.count_documents({}))