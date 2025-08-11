from app import app, items_collection, user_collection

print("=== DATABASE CHECK ===")
print(f"Items collection count: {items_collection.count_documents({})}")
print(f"Users collection count: {user_collection.count_documents({})}")

print("\n=== SAMPLE ITEMS ===")
items = list(items_collection.find().limit(3))
for item in items:
    print(f"ID: {item['_id']}")
    print(f"Name: {item['name']}")
    print(f"Image: {item.get('image', 'No image')}")
    print(f"Stock: {item.get('stock', item.get('quantity', 'No stock'))}")
    print(f"Category: {item.get('category', 'No category')}")
    print("---")

print("\n=== SAMPLE USERS ===")
users = list(user_collection.find().limit(3))
for user in users:
    print(f"Username: {user['username']}")
    print(f"Role: {user.get('role', 'No role')}")
    print("---")
