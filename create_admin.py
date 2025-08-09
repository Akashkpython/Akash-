import bcrypt
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["grocery_app"]
users = db["users"]
print(users.find_one({'username':'admin'}))

admin_username = "admin"
admin_password = "adminpass"

if not users.find_one({"username": admin_username}):
    hashed_pw = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt())
    users.insert_one({
        "username": admin_username,
        "password": hashed_pw,
        "is_admin": True
    })
    print("✅ Admin created")
else:
    print("⚠ Admin already exists")