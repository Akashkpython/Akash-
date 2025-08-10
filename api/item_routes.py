from flask import Blueprint, jsonify, request, render_template, redirect, url_for, session, flash
from bson.objectid import ObjectId
import bcrypt

item_routes = Blueprint('item_routes', __name__)

# Global collection references (assigned from app.py)
items_collection = None
user_collection = None

def init_item_routes(db_items_collection, db_user_collection):
    """Initialize blueprint with database collections used by the routes."""
    global items_collection, user_collection
    items_collection = db_items_collection
    user_collection = db_user_collection

# ----------------------------
# 🔐 User Login
# ----------------------------
@item_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password').encode('utf-8')

        user = user_collection.find_one({'username': username})
        if not user:
            flash("❌ User not found.")
            return redirect(url_for('item_routes.login'))

        if not bcrypt.checkpw(password, user['password']):
            flash("❌ Incorrect password.")
            return redirect(url_for('item_routes.login'))

        session['user'] = username
        session['role'] = user.get('role', 'user')
        flash("✅ Login successful.")
        
        # Resume add to cart if user came from that action
        if session.get('next_action'):
            return redirect(url_for('resume_add_to_cart'))

        return redirect(url_for('home'))

    return render_template('login.html')


# ----------------------------
# 📝 User Signup
# ----------------------------
@item_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')

        if not username or not password:
            flash("❗ All fields are required.")
            return redirect(url_for('item_routes.signup'))

        if user_collection.find_one({'username': username}):
            flash("❌ Username already exists.")
            return redirect(url_for('item_routes.signup'))

        hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_collection.insert_one({
            'username': username,
            'password': hashed_pwd,
            'role': 'user'
        })
        flash("✅ Signup successful. Please log in.")
        return redirect(url_for('item_routes.login'))

    return render_template('signup.html')


# ----------------------------
# 📦 API Routes for Items
# ----------------------------

@item_routes.route('/api/items', methods=['GET'])
def get_items():
    items = list(items_collection.find())
    for item in items:
        item['_id'] = str(item['_id'])  # Convert ObjectId to string
    return jsonify(items)

@item_routes.route('/api/items/<item_id>', methods=['GET'])
def get_item(item_id):
    try:
        item = items_collection.find_one({'_id': ObjectId(item_id)})
    except Exception:
        return jsonify({'error': 'Invalid item ID'}), 400
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    item['_id'] = str(item['_id'])
    return jsonify(item), 200

@item_routes.route('/api/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    results = items_collection.find({'name': {'$regex': query, '$options': 'i'}}, {'name': 1}).limit(10)
    suggestions = [{'_id': str(doc['_id']), 'name': doc.get('name', '')} for doc in results]
    return jsonify(suggestions)

@item_routes.route('/api/items', methods=['POST'])
def add_item():
    data = request.json
    required_fields = ['name', 'price', 'description', 'stock', 'image']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    item = {
        'name': data['name'],
        'price': float(data['price']),
        'description': data['description'],
        'stock': int(data['stock']),
        'image': data['image']
    }

    result = items_collection.insert_one(item)
    return jsonify({'message': 'Item added', 'item_id': str(result.inserted_id)}), 201

@item_routes.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    updated_fields = {
        k: v for k, v in data.items()
        if k in ['name', 'price', 'description', 'stock', 'image']
    }

    try:
        result = items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': updated_fields}
        )
    except Exception:
        return jsonify({'error': 'Invalid item ID'}), 400

    if result.modified_count == 0:
        return jsonify({'message': 'No changes made'}), 200

    return jsonify({'message': 'Item updated'}), 200

@item_routes.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        result = items_collection.delete_one({'_id': ObjectId(item_id)})
    except Exception:
        return jsonify({'error': 'Invalid item ID'}), 400

    if result.deleted_count == 0:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify({'message': 'Item deleted'}), 200
