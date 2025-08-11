import bcrypt
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.environ.get("MONGO_DB_NAME", "grocery_app")]
users = db["users"]

admin_username = os.environ.get("ADMIN_USERNAME", "admin")
admin_password = os.environ.get("ADMIN_PASSWORD", "adminpass")

if not users.find_one({"username": admin_username}):
    hashed_pw = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt())
    users.insert_one({
        "username": admin_username,
        "password": hashed_pw,
        "role": "admin"
    })
    print("✅ Admin created")
else:
    print("⚠ Admin already exists")