# decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """
    Protect routes from unauthorized access.
    Checks if the user is logged in by looking for 'user' in the session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('item_routes.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Protect routes that should be accessible only to admins.
    Requires 'is_admin' flag in the session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('item_routes.login'))
        if session.get('role') != 'admin':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function