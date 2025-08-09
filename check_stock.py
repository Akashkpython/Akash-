from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["grocery_app"]
collection = db["items"]

item = collection.find_one({"name": "lays"})
print(item)