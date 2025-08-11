from app import app, items_collection

print("=== FIXING IMAGE REFERENCES ===")

# Update items with actual existing images
updates = [
    {"name": "Apple", "image": "10319972.jpg"},
    {"name": "Chips", "image": "1201765.jpg"},
    {"name": "Juice", "image": "2069188.jpg"}
]

for update in updates:
    result = items_collection.update_one(
        {"name": update["name"]},
        {"$set": {"image": update["image"]}}
    )
    if result.modified_count > 0:
        print(f"✅ Updated {update['name']} with image: {update['image']}")
    else:
        print(f"❌ Failed to update {update['name']}")

print("\n=== VERIFYING UPDATES ===")
items = list(items_collection.find())
for item in items:
    print(f"{item['name']}: {item.get('image', 'No image')}")

print("\n=== IMAGE FILES EXIST ===")
import os
for item in items:
    if item.get('image'):
        image_path = f"static/uploads/{item['image']}"
        if os.path.exists(image_path):
            print(f"✅ {item['name']}: {item['image']} exists")
        else:
            print(f"❌ {item['name']}: {item['image']} missing")
