import os
import json
import bcrypt
import pytest

os.environ['MONGO_MOCK'] = '1'

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as app_module
from app import app, user_collection, items_collection, cart_collection, orders_collection


@pytest.fixture(autouse=True)
def clear_db():
    # Clear collections before each test
    for coll in [user_collection, items_collection, cart_collection, orders_collection]:
        coll.delete_many({})
    # Create admin
    user_collection.insert_one({
        'username': 'admin',
        'password': bcrypt.hashpw(b'admin123', bcrypt.gensalt()),
        'role': 'admin'
    })
    yield


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def signup(client, username, password):
    return client.post('/signup', data={'username': username, 'password': password, 'confirm_password': password}, follow_redirects=True)


def test_signup_and_login_flow(client):
    r = signup(client, 'alice', 'password')
    assert r.status_code == 200
    r = login(client, 'alice', 'password')
    assert r.status_code == 200


def seed_item():
    result = items_collection.insert_one({
        'name': 'Apple',
        'price': 10.0,
        'description': 'Fresh',
        'stock': 100,
        'image': 'apple.jpg'
    })
    return str(result.inserted_id)


def test_add_to_cart_and_checkout(client):
    signup(client, 'bob', 'password')
    login(client, 'bob', 'password')
    item_id = seed_item()
    r = client.post(f'/add_to_cart/{item_id}', data={'quantity': 2}, follow_redirects=True)
    assert r.status_code == 200
    # View cart page should show total
    r = client.get('/cart')
    assert b'Total' in r.data
    # Checkout
    r = client.get('/checkout')
    assert r.status_code == 200


def test_buy_now_flow(client):
    signup(client, 'carol', 'password')
    login(client, 'carol', 'password')
    item_id = seed_item()
    r = client.post(f'/buy_now_page/{item_id}', follow_redirects=True)
    assert r.status_code == 200
    r = client.get('/checkout_buy_now')
    assert r.status_code == 200
    r = client.post('/place_buy_now_order', follow_redirects=True)
    assert r.status_code == 200


def admin_login(client):
    return login(client, 'admin', 'admin123')


def test_admin_add_edit_delete_product(client):
    admin_login(client)
    # Add product
    data = {
        'name': 'Banana',
        'price': '20',
        'description': 'Sweet',
        'stock': '50',
        'category': 'fruits',
        'offer': '10% OFF'
    }
    # Minimal file upload using empty file via BytesIO
    import io
    data['image'] = (io.BytesIO(b'fakeimg'), 'banana.jpg')
    r = client.post('/add_product', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert r.status_code == 200

    product = items_collection.find_one({'name': 'Banana'})
    assert product is not None

    # Edit product
    r = client.post(f"/edit_item/{product['_id']}", data={'name': 'Banana', 'price': '25', 'quantity': '60', 'category': 'fruits'}, follow_redirects=True)
    assert r.status_code == 200
    updated = items_collection.find_one({'_id': product['_id']})
    assert float(updated['price']) == 25.0
    assert int(updated['stock']) == 60

    # Delete product
    r = client.post(f"/delete_item/{product['_id']}", follow_redirects=True)
    assert r.status_code == 200
    assert items_collection.find_one({'_id': product['_id']}) is None


def test_admin_analytics_endpoint(client):
    admin_login(client)
    # Seed an order
    item_id = seed_item()
    orders_collection.insert_one({
        'username': 'admin',
        'items': [{'item_id': item_id, 'name': 'Apple', 'price': 10.0, 'quantity': 3}],
        'date': app_module.datetime.now(),
        'status': 'Placed',
        'total': 30.0
    })
    r = client.get('/admin/analytics')
    assert r.status_code == 200


def test_admin_user_management(client):
    admin_login(client)
    # Create user Dave
    user_collection.insert_one({'username': 'dave', 'password': bcrypt.hashpw(b'pw', bcrypt.gensalt()), 'role': 'user'})
    # Update role
    dave = user_collection.find_one({'username': 'dave'})
    r = client.post(f"/admin/users/{dave['_id']}/update", data={'role': 'admin'}, follow_redirects=True)
    assert r.status_code == 200
    assert user_collection.find_one({'_id': dave['_id']})['role'] == 'admin'
    # Delete user
    r = client.post(f"/admin/users/{dave['_id']}/delete", follow_redirects=True)
    assert r.status_code == 200
    assert user_collection.find_one({'_id': dave['_id']}) is None

