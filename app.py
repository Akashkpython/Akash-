from flask import Flask, request, render_template, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps
from decorators import login_required
import bcrypt

from api.item_routes import item_routes, init_item_routes

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MongoDB connection with error handling
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["grocery_app"]
    product_collection=db['items']
    items_collection = db["items"]
    user_collection = db["users"]
    cart_collection = db["cart"]
    orders_collection = db["orders"]

    init_item_routes(items_collection, user_collection)
    app.register_blueprint(item_routes)
    
except Exception as e:
    print("Error connecting to MongoDB. Check server and URI.")
    raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            flash("Access denied. Admins only!", "error")
            return redirect(url_for('item_routes.login'))
        return f(*args, **kwargs)
    return decorated_function


# Route to handle Add to Cart
# Removed duplicate add_to_cart route using 'username' session key

# Route for Buy Now
@app.route('/buy_now/<item_id>', methods=['POST'])
def buy_now(item_id):
    if 'user' not in session:
        flash("Please login to buy product")
        return redirect(url_for('item_routes.login'))

    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        flash("Item not found.")
        return redirect(url_for('view_items'))

    session['buy_now_item'] = {
        'item_id': str(item['_id']),
        'name': item['name'],
        'price': item['price'],
        'quantity': 1
    }
    return redirect(url_for('checkout_buy_now'))

@app.route('/add_item')
def add_item():
    return "Add item page (under construction)"

@app.route('/admin')
@admin_only
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@admin_only
def view_users():
    users = user_collection.find()
    return render_template('admin/users.html', users=users)

@app.route('/cancel_order/<order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        if order and order['username'] == session['user']:
            orders_collection.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': 'Cancelled'}})
            flash('Order cancelled successfully.')
        else:
            flash('Order not found or unauthorized.', 'error')
    except Exception as e:
        flash('Error cancelling order.', 'error')
    return redirect(url_for('view_orders'))

@app.route('/orders')
@login_required
def view_orders():
    user_orders = list(orders_collection.find({'username': session['user']}))
    return render_template('view_orders.html', orders=user_orders)

@app.route('/admin/orders')
@admin_only
def view_all_orders():
    all_orders = list(orders_collection.find())
    for order in all_orders:
        order['_id'] = str(order['_id'])
        if 'items' not in order or not isinstance(order['items'], list):
            order['items'] = []
    return render_template('admin/view_all_orders.html', orders=all_orders)
@app.route('/admin/analytics')
@admin_only
def admin_analytics():
    total_users = user_collection.count_documents({'role': 'user'})
    total_orders = orders_collection.count_documents({})
    total_items = items_collection.count_documents({})
    total_sales = 0
    for order in orders_collection.find():
        for item in order.get('items', []):
            total_sales += float(item.get('price', 0)) * int(item.get('quantity', 1))
    return render_template('admin/admin_analytics.html', 
                         total_users=total_users, 
                         total_orders=total_orders, 
                         total_items=total_items, 
                         total_sales=total_sales)

@app.route('/')
def home():
    items = items_collection.find().limit(6)
    return render_template('home.html', items=items)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pwd = request.form['password']
        confirm = request.form['confirm_password']
        
        if not uname or not pwd:
            flash("Username and password are required.")
            return redirect(url_for('signup'))
            
        if pwd != confirm:
            flash("Passwords do not match.")
            return redirect(url_for('signup'))
            
        if len(pwd) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for('signup'))
            
        if user_collection.find_one({'username': uname}):
            flash("Username already exists.")
            return redirect(url_for('signup'))
            
        hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
        user_collection.insert_one({
            'username': uname, 
            'password': hashed_pwd, 
            'role': 'user',
            'created_at': datetime.now()
        })
        flash("Account created successfully. Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/add_product', methods=['GET', 'POST'])
@admin_only
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        else:
            flash("Invalid image format.")
            return redirect(url_for('add_product'))

        product = {
            'name': name,
            'price': price,
            'description': description,
            'stock': stock,
            'image': filename  # Save only the filename
        }

        product_collection.insert_one(product)
        flash('Product added successfully!')
        return redirect(url_for('view_items'))

    return render_template('admin/add_product.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('item_routes.login'))

@app.route('/items')
@login_required
def view_items():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'all')
    
    query = {}
    if search:
        query['name'] = {'$regex': search, '$options': 'i'}
    if category != 'all':
        query['category'] = category
    
    items = list(items_collection.find(query))
    return render_template('view_items.html', items=items)

@app.route('/add_to_cart/<item_id>', methods=['POST'])
def add_to_cart(item_id):
    if 'user' not in session:
        # ✅ Step 1: Save the action data in session
        session['next_action'] = {
            'action': 'add_to_cart',
            'item_id': item_id,
            'quantity': request.form.get('quantity', 1)
        }
        return redirect(url_for('item_routes.login'))  # Redirect to login first

    # 🔽 Existing logic (no change here)
    username = session['user']
    qty = int(request.form.get('quantity', 1))

    item = collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        flash("Item not found.")
        return redirect(url_for('view_items'))

    cart = cart_collection.find_one({'username': username}) or {'username': username, 'items': []}

    for i in cart['items']:
        if i['item_id'] == item['_id']:
            i['quantity'] += qty
            break
    else:
        cart['items'].append({
            'item_id': item['_id'],
            'name': item['name'],
            'price': item['price'],
            'quantity': qty
        })

    cart_collection.update_one({'username': username}, {'$set': {'items': cart['items']}}, upsert=True)

    flash("Added to cart.")
    return redirect(url_for('view_cart'))

@app.route('/buy_now_page/<item_id>', methods=['POST'])
def buy_now_page(item_id):
    if 'user' not in session:
        return redirect(url_for('item_routes.login'))

    item = collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        flash("Item not found.")
        return redirect(url_for('view_items'))

    # Save item to session for buy now
    session['buy_now_item'] = {
        'item_id': str(item['_id']),
        'name': item['name'],
        'price': item['price'],
        'quantity': 1
    }

    return redirect(url_for('checkout_buy_now'))

@app.route('/checkout_buy_now')
def checkout_buy_now():
    if 'user' not in session:
        return redirect(url_for('item_routes.login'))

    item = session.get('buy_now_item')
    if not item:
        flash("No item selected for Buy Now.")
        return redirect(url_for('view_items'))

    total = item['price'] * item['quantity']
    return render_template('checkout_buy_now.html', item=item, total=total)

@app.route('/cart')
def view_cart():
    if 'user' not in session:
        return redirect(url_for('item_routes.login'))
    username = session['user']
    cart = cart_collection.find_one({'username': username})
    items = cart['items'] if cart else []
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', cart_items=items, total=total)

@app.route('/resume_add_to_cart')
def resume_add_to_cart():
    if 'user' not in session or 'next_action' not in session:
        return redirect(url_for('item_routes.login'))

    action = session.pop('next_action', None)
    if not action or action.get('action') != 'add_to_cart':
        return redirect(url_for('view_items'))

    item_id = action.get('item_id')
    quantity = int(action.get('quantity', 1))

    item = collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        flash("Item not found.")
        return redirect(url_for('view_items'))

    username = session['user']
    cart = cart_collection.find_one({'username': username}) or {'username': username, 'items': []}

    for i in cart['items']:
        if i['item_id'] == item['_id']:
            i['quantity'] += quantity
            break
    else:
        cart['items'].append({
            'item_id': item['_id'],
            'name': item['name'],
            'price': item['price'],
            'quantity': quantity
        })

    cart_collection.update_one({'username': username}, {'$set': {'items': cart['items']}}, upsert=True)

    flash("Item added to cart after login.")
    return redirect(url_for('view_cart'))

@app.route('/checkout')
@login_required
def checkout():
    username = session['user']
    cart = cart_collection.find_one({'username': username})
    items = cart['items'] if cart else []
    total = sum(float(item['price']) * int(item['quantity']) for item in items)
    return render_template('checkout.html', items=items, total=total)

@app.route('/place_buy_now_order', methods=['POST'])
def place_buy_now_order():
    if 'user' not in session:
        return redirect(url_for('item_routes.login'))

    item = session.get('buy_now_item')
    if not item:
        flash("No item to place order.")
        return redirect(url_for('view_items'))

    orders_collection.insert_one({
        "username": session['user'],
        "items": [item]
    })

    session.pop('buy_now_item', None)  # Clear session after placing order
    flash("Order placed successfully!")
    return redirect(url_for('view_orders'))

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    try:
        username = session['user']
        cart = cart_collection.find_one({'username': username})
        
        if not cart or not cart.get("items"):
            flash("Your cart is empty.")
            return redirect(url_for('view_cart'))
        
        for item in cart["items"]:
            db_item = items_collection.find_one({'_id': ObjectId(item['item_id'])})
            if not db_item or db_item.get('stock', 0) < item['quantity']:
                flash(f"Not enough stock for {item['name']}")
                return redirect(url_for('view_cart'))
        
        total = sum(float(item['price']) * int(item['quantity']) for item in cart["items"])
        
        order = {
            "username": username,
            "items": cart["items"],
            "date": datetime.now(),
            "status": "Placed",
            "total": total
        }
        orders_collection.insert_one(order)
        
        for item in cart["items"]:
            items_collection.update_one(
                {'_id': ObjectId(item['item_id'])}, 
                {'$inc': {'stock': -item['quantity']}}
            )
        
        cart_collection.update_one(
            {'username': username}, 
            {"$set": {"items": []}}
        )
        
        flash("Order placed successfully!")
    except Exception as e:
        flash("Error placing order.", 'error')
    
    return redirect(url_for('view_orders'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['user']
    user = user_collection.find_one({'username': username})
    
    if request.method == 'POST':
        file = request.files.get('profile_pic')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            user_collection.update_one(
                {'username': username}, 
                {'$set': {'profile_pic': filename}}
            )
            flash("Profile updated.")
            return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/toggle_dark_mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    dark_mode = session.get('dark_mode', False)
    session['dark_mode'] = not dark_mode
    flash("Dark mode toggled.")
    return redirect(url_for('settings'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        try:
            old_pass = request.form.get('current_password', '').encode('utf-8')
            new_pass = request.form.get('new_password', '')
            confirm_pass = request.form.get('confirm_password', '')
            
            if not old_pass or not new_pass or not confirm_pass:
                flash("All fields are required.")
                return redirect(url_for('change_password'))
            
            if new_pass != confirm_pass:
                flash("New passwords do not match.")
                return redirect(url_for('change_password'))
            
            if len(new_pass) < 6:
                flash("Password must be at least 6 characters.")
                return redirect(url_for('change_password'))
            
            user = user_collection.find_one({'username': session['user']})
            if user and bcrypt.checkpw(old_pass, user['password']):
                hashed_new_pass = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
                user_collection.update_one(
                    {'username': session['user']},
                    {'$set': {'password': hashed_new_pass}}
                )
                flash("Password changed successfully.")
                return redirect(url_for('settings'))
            else:
                flash("Current password incorrect.")
        except Exception as e:
            flash("Error changing password.", 'error')
    
    return render_template('change_password.html')

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/admin/manage_items')
def manage_items():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('item_routes.login'))

    items = items_collection.find()
    return render_template('manage_items.html', items=items)

@app.route('/edit_item/<item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        flash("Item not found.")
        return redirect(url_for('manage_items'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        items_collection.update_one({'_id': ObjectId(item_id)}, {
            '$set': {'name': name, 'price': price, 'quantity': quantity}
        })
        flash("Item updated successfully.")
        return redirect(url_for('manage_items'))

    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    if not session.get('user') or session.get('role') != 'admin':
        flash("Access denied.")
        return redirect(url_for('item_routes.login'))

    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if item:
        items_collection.delete_one({'_id': ObjectId(item_id)})
        flash("Item deleted successfully.")
    else:
        flash("Item not found.")

    return redirect(url_for('manage_items'))

@app.route('/remove_from_cart/<item_id>', methods=['POST'])
def remove_from_cart(item_id):
    print("Removing item ID:", item_id)
    if 'user' not in session:
        return redirect(url_for('item_routes.login'))

    username = session['user']
    cart = cart_collection.find_one({'username': username})

    if cart:
        updated_items = [item for item in cart['items'] if str(item['item_id']) != item_id]
        cart_collection.update_one({'username': username}, {'$set': {'items': updated_items}})
        flash("🗑 Item removed from cart.")

    return redirect(url_for('view_cart'))

@app.route('/invoice/<order_id>')
def view_invoice(order_id):
    # Simulate getting order from database
    order = {
        'id': order_id,
        'date': '2025-08-06',
        'customer_name': 'Akash',
        'address': 'Kundapura, Karnataka',
        'items': [
            {'name': 'Apple', 'quantity': 2, 'price': 50},
            {'name': 'Chips', 'quantity': 1, 'price': 30},
            {'name': 'Juice', 'quantity': 3, 'price': 25},
        ]
    }

    order['total'] = sum(item['quantity'] * item['price'] for item in order['items'])
    return render_template('invoice.html', order=order)

@app.route('/download_invoice/<order_id>')
def download_invoice(order_id):
    from flask import make_response
    from weasyprint import HTML

    # Reuse the same order data
    order = {
        'id': order_id,
        'date': '2025-08-06',
        'customer_name': 'Akash',
        'address': 'Kundapura, Karnataka',
        'items': [
            {'name': 'Apple', 'quantity': 2, 'price': 50},
            {'name': 'Chips', 'quantity': 1, 'price': 30},
            {'name': 'Juice', 'quantity': 3, 'price': 25},
        ]
    }

    order['total'] = sum(item['quantity'] * item['price'] for item in order['items'])

    # Render HTML and convert to PDF
    html = render_template('invoice.html', order=order)
    pdf = HTML(string=html).write_pdf()

    # Create response with PDF
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order_id}.pdf'

    return response

if __name__ == '_main_':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

def create_admin_if_not_exists():
    if not user_collection.find_one({'username': 'admin'}):
        hashed_pwd = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        user_collection.insert_one({
            'username': 'admin',
            'password': hashed_pwd,
            'role': 'admin',
            'created_at': datetime.now()
        })

create_admin_if_not_exists()