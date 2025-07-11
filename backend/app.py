#!/usr/bin/env python3
"""
Flask API for License Manager with Authentication and Role Management
Provides complete CRUD endpoints for users and licenses with secure authentication
"""

from flask import Flask, jsonify, request, session, redirect, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import secrets
import os
import uuid
from werkzeug.utils import secure_filename


def get_database_connection():
    """Create and return a database connection"""
    # Try different possible paths for the database
    possible_paths = [
        Path("../db/license_manager.db"),  # From backend directory
        Path("db/license_manager.db"),     # From project root
        Path("backend/../db/license_manager.db"),  # Alternative
    ]
    
    for db_path in possible_paths:
        if db_path.exists():
            return sqlite3.connect(db_path)
    
    # If no existing path found, try to create the connection anyway
    for db_path in possible_paths:
        try:
            return sqlite3.connect(db_path)
        except:
            continue
    
    raise FileNotFoundError("Could not find license_manager.db in any expected location")


def init_auth_tables():
    """Initialize authentication and audit tables if they don't exist"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Create auth_users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'owner', 'viewer')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action_type TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            target TEXT,
            details TEXT
        )
    ''')
    
    # Check if we need to create the initial owner
    cursor.execute("SELECT COUNT(*) FROM auth_users WHERE role = 'owner'")
    owner_count = cursor.fetchone()[0]
    
    if owner_count == 0:
        # Create initial owner account
        initial_password = "admin123"  # Change this in production!
        password_hash = generate_password_hash(initial_password)
        cursor.execute("""
            INSERT INTO auth_users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, ("admin", password_hash, "owner"))
        
        # Log the creation
        cursor.execute("""
            INSERT INTO audit_log (action_type, performed_by, target, details)
            VALUES (?, ?, ?, ?)
        """, ("create_owner", "system", "admin", "Initial owner account created"))
    
    conn.commit()
    conn.close()


def log_audit_event(action_type, performed_by, target=None, details=None):
    """Log an audit event to the database"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log (action_type, performed_by, target, details)
            VALUES (?, ?, ?, ?)
        """, (action_type, performed_by, target, json.dumps(details) if details else None))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to log audit event: {e}")


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "login_url": "/login"
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(allowed_roles=None):
    """Decorator to require specific role(s) for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return jsonify({
                    "success": False,
                    "error": "Authentication required"
                }), 401
            
            # Get user's role from database
            conn = get_database_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM auth_users WHERE username = ?", (session['username'],))
            user_role = cursor.fetchone()
            conn.close()
            
            if not user_role:
                session.clear()
                return jsonify({
                    "success": False,
                    "error": "User not found"
                }), 401
            
            user_role = user_role[0]
            
            # Handle no roles specified
            if allowed_roles is None:
                return jsonify({
                    "success": False,
                    "error": "No roles specified for this endpoint"
                }), 403
            
            # Normalize roles into a list
            roles_list = allowed_roles
            if isinstance(allowed_roles, str):
                roles_list = [allowed_roles]
            elif not isinstance(allowed_roles, (list, tuple)):
                return jsonify({
                    "success": False,
                    "error": "Invalid role specification"
                }), 500
            
            # Check role permissions
            if user_role not in roles_list:
                return jsonify({
                    "success": False,
                    "error": f"Access denied. Required roles: {', '.join(roles_list)}"
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_role():
    """Get the current user's role"""
    if 'username' not in session:
        return None
    
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM auth_users WHERE username = ?", (session['username'],))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = UPLOAD_FOLDER / unique_filename
        file.save(file_path)
        return unique_filename
    return None


def get_icon_url(filename):
    """Get full URL for icon file"""
    if filename:
        return f"/static/icons/{filename}"
    return None


# Database helper functions (preserved from original)
def get_users_with_licenses():
    """Retrieve all users and their licenses from the database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("""
        SELECT id, name, email, department, manager, title, created_at, updated_at
        FROM users
        ORDER BY name
    """)
    users = cursor.fetchall()
    
    # Get all licenses with user and license type information
    cursor.execute("""
        SELECT l.id, l.user_id, l.software_name, l.license_key, 
               l.license_type, l.status, l.assigned_date, l.revoked_date, l.notes,
               lt.name as license_type_name, lt.icon_filename
        FROM licenses l
        LEFT JOIN license_types lt ON l.license_type_id = lt.id
        ORDER BY l.user_id, l.software_name
    """)
    licenses = cursor.fetchall()
    
    conn.close()
    return users, licenses


def get_user_by_id(user_id):
    """Get a single user by ID with their licenses"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get user
    cursor.execute("""
        SELECT id, name, email, department, manager, title, created_at, updated_at
        FROM users
        WHERE id = ?
    """, (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return None, []
    
    # Get user's licenses with license type information
    cursor.execute("""
        SELECT l.id, l.user_id, l.software_name, l.license_key, 
               l.license_type, l.status, l.assigned_date, l.revoked_date, l.notes,
               lt.name as license_type_name, lt.icon_filename
        FROM licenses l
        LEFT JOIN license_types lt ON l.license_type_id = lt.id
        WHERE l.user_id = ?
        ORDER BY l.software_name
    """, (user_id,))
    licenses = cursor.fetchall()
    
    conn.close()
    return user, licenses


def format_user_data(users, licenses):
    """Format user and license data into a structured response"""
    # Group licenses by user_id
    user_licenses = {}
    for license_data in licenses:
        user_id = license_data[1]  # user_id is at index 1
        if user_id not in user_licenses:
            user_licenses[user_id] = []
        
        license_dict = {
            "id": license_data[0],
            "software_name": license_data[2],
            "license_key": license_data[3],
            "license_type": license_data[4],
            "status": license_data[5],
            "assigned_date": license_data[6],
            "revoked_date": license_data[7],
            "notes": license_data[8],
            "license_type_name": license_data[9],
            "icon_url": get_icon_url(license_data[10]) if license_data[10] else None
        }
        user_licenses[user_id].append(license_dict)
    
    # Format user data
    formatted_users = []
    for user in users:
        user_id, name, email, department, manager, title, created_at, updated_at = user
        
        user_dict = {
            "id": user_id,
            "name": name,
            "email": email,
            "department": department,
            "manager": manager,
            "title": title,
            "created_at": created_at,
            "updated_at": updated_at,
            "licenses": user_licenses.get(user_id, [])
        }
        formatted_users.append(user_dict)
    
    return formatted_users


def format_single_user(user, licenses):
    """Format a single user with their licenses"""
    if not user:
        return None
    
    user_id, name, email, department, manager, title, created_at, updated_at = user
    
    # Format licenses
    formatted_licenses = []
    for license_data in licenses:
        license_dict = {
            "id": license_data[0],
            "software_name": license_data[2],
            "license_key": license_data[3],
            "license_type": license_data[4],
            "status": license_data[5],
            "assigned_date": license_data[6],
            "revoked_date": license_data[7],
            "notes": license_data[8],
            "license_type_name": license_data[9],
            "icon_url": get_icon_url(license_data[10]) if license_data[10] else None
        }
        formatted_licenses.append(license_dict)
    
    return {
        "id": user_id,
        "name": name,
        "email": email,
        "department": department,
        "manager": manager,
        "title": title,
        "created_at": created_at,
        "updated_at": updated_at,
        "licenses": formatted_licenses
    }


def get_all_licenses():
    """Get all licenses with user information"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT l.id, l.user_id, u.name as user_name, u.email, l.software_name, 
               l.license_key, l.license_type, l.status, l.assigned_date, 
               l.revoked_date, l.notes, lt.name as license_type_name, lt.icon_filename
        FROM licenses l
        JOIN users u ON l.user_id = u.id
        LEFT JOIN license_types lt ON l.license_type_id = lt.id
        ORDER BY u.name, l.software_name
    """)
    licenses = cursor.fetchall()
    
    conn.close()
    return licenses


def format_license_data(licenses):
    """Format license data with user information"""
    formatted_licenses = []
    for license_data in licenses:
        license_dict = {
            "id": license_data[0],
            "user_id": license_data[1],
            "user_name": license_data[2],
            "user_email": license_data[3],
            "software_name": license_data[4],
            "license_key": license_data[5],
            "license_type": license_data[6],
            "status": license_data[7],
            "assigned_date": license_data[8],
            "revoked_date": license_data[9],
            "notes": license_data[10],
            "license_type_name": license_data[11],
            "icon_url": get_icon_url(license_data[12]) if license_data[12] else None
        }
        formatted_licenses.append(license_dict)
    
    return formatted_licenses


# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key

# File upload configuration
UPLOAD_FOLDER = Path("../static/icons")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Initialize auth tables
init_auth_tables()


# AUTHENTICATION ENDPOINTS

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                "success": False,
                "error": "Username and password required"
            }), 400
        
        username = data['username']
        password = data['password']
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get user from database
        cursor.execute("""
            SELECT id, username, password_hash, role 
            FROM auth_users 
            WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user or not check_password_hash(user[2], password):
            return jsonify({
                "success": False,
                "error": "Invalid username or password"
            }), 401
        
        # Set session
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['role'] = user[3]
        
        # Log login
        log_audit_event("login", username)
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "username": user[1],
                "role": user[3]
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    if 'username' in session:
        username = session['username']
        log_audit_event("logout", username)
    
    session.clear()
    
    return jsonify({
        "success": True,
        "message": "Logout successful"
    })


@app.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({
        "success": True,
        "user": {
            "username": session['username'],
            "role": session['role']
        }
    })


# ADMIN MANAGEMENT ENDPOINTS

@app.route('/auth/admins', methods=['GET'])
@login_required
@role_required('owner')
def get_admins():
    """Get all admin users (owner only)"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, role, created_at, updated_at
            FROM auth_users
            WHERE role IN ('admin', 'owner')
            ORDER BY role DESC, username
        """)
        
        admins = []
        for row in cursor.fetchall():
            admins.append({
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "admins": admins
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/auth/admins', methods=['POST'])
@login_required
@role_required('owner')
def create_admin():
    """Create a new admin or viewer user (owner only)"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data or 'role' not in data:
            return jsonify({
                "success": False,
                "error": "Username, password, and role required"
            }), 400
        
        username = data['username']
        password = data['password']
        role = data['role']
        
        # Validate role
        if role not in ['admin', 'viewer']:
            return jsonify({
                "success": False,
                "error": "Role must be 'admin' or 'viewer'"
            }), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM auth_users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "error": "Username already exists"
            }), 409
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO auth_users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, (username, password_hash, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event(f"create_{role}", session['username'], username)
        
        return jsonify({
            "success": True,
            "message": f"{role.capitalize()} user created successfully",
            "user": {
                "id": user_id,
                "username": username,
                "role": role
            }
        }), 201
    
    except Exception as e:
        print(f"Error creating admin/viewer: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/auth/admins/<int:admin_id>', methods=['DELETE'])
@login_required
@role_required('owner')
def delete_admin(admin_id):
    """Delete an admin or viewer user (owner only)"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("""
            SELECT username, role FROM auth_users WHERE id = ?
        """, (admin_id,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        username, role = user
        
        # Prevent deleting the owner
        if role == 'owner':
            conn.close()
            return jsonify({
                "success": False,
                "error": "Cannot delete the owner account"
            }), 403
        
        # Prevent deleting yourself
        if admin_id == session['user_id']:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Cannot delete your own account"
            }), 403
        
        # Delete user
        cursor.execute("DELETE FROM auth_users WHERE id = ?", (admin_id,))
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event(f"delete_{role}", session['username'], username)
        
        return jsonify({
            "success": True,
            "message": f"{role.capitalize()} user '{username}' deleted successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/auth/transfer-ownership', methods=['POST'])
@login_required
@role_required('owner')
def transfer_ownership():
    """Transfer ownership to another admin (owner only)"""
    try:
        data = request.get_json()
        
        if not data or 'new_owner_username' not in data:
            return jsonify({
                "success": False,
                "error": "New owner username required"
            }), 400
        
        new_owner_username = data['new_owner_username']
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if new owner exists and is an admin
        cursor.execute("""
            SELECT id, username, role FROM auth_users WHERE username = ?
        """, (new_owner_username,))
        
        new_owner = cursor.fetchone()
        if not new_owner:
            conn.close()
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        if new_owner[2] != 'admin':
            conn.close()
            return jsonify({
                "success": False,
                "error": "Can only transfer ownership to an admin user"
            }), 400
        
        # Transfer ownership
        cursor.execute("""
            UPDATE auth_users SET role = 'admin', updated_at = CURRENT_TIMESTAMP
            WHERE role = 'owner'
        """)
        
        cursor.execute("""
            UPDATE auth_users SET role = 'owner', updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (new_owner_username,))
        
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event("transfer_ownership", session['username'], new_owner_username, {
            "old_owner": session['username'],
            "new_owner": new_owner_username
        })
        
        # Clear session if current user is no longer owner
        if session['username'] != new_owner_username:
            session.clear()
            return jsonify({
                "success": True,
                "message": f"Ownership transferred to '{new_owner_username}'",
                "logout_required": True
            })
        
        return jsonify({
            "success": True,
            "message": f"Ownership transferred to '{new_owner_username}'"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/auth/reset-password', methods=['POST'])
@login_required
@role_required(['admin', 'owner'])
def reset_password():
    """Reset a user's password (admin can reset viewers, owner can reset anyone)"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'new_password' not in data:
            return jsonify({
                "success": False,
                "error": "Username and new password required"
            }), 400
        
        username = data['username']
        new_password = data['new_password']
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if user exists and get their role
        cursor.execute("SELECT id, role FROM auth_users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        user_id, target_role = user_data
        current_user_role = session['role']
        
        # Check permissions based on roles
        if current_user_role == 'admin':
            # Admin can only reset viewer passwords
            if target_role != 'viewer':
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "Admins can only reset viewer passwords"
                }), 403
        elif current_user_role == 'owner':
            # Owner can reset anyone's password
            pass
        else:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Insufficient permissions"
            }), 403
        
        # Update password
        password_hash = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE auth_users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (password_hash, username))
        
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event("reset_password", session['username'], username)
        
        return jsonify({
            "success": True,
            "message": f"Password reset for '{username}' successful"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/auth/change-password', methods=['POST'])
@login_required
@role_required(['admin', 'owner'])
def change_own_password():
    """Change current user's password"""
    try:
        data = request.get_json()
        
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                "success": False,
                "error": "Current password and new password required"
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Verify current password
        cursor.execute("""
            SELECT password_hash FROM auth_users WHERE username = ?
        """, (session['username'],))
        
        result = cursor.fetchone()
        if not result or not check_password_hash(result[0], current_password):
            conn.close()
            return jsonify({
                "success": False,
                "error": "Current password is incorrect"
            }), 401
        
        # Update password
        password_hash = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE auth_users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (password_hash, session['username']))
        
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event("change_password", session['username'], session['username'])
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# LICENSE TYPE MANAGEMENT ENDPOINTS

@app.route('/license-types', methods=['GET'])
@login_required
@role_required(['admin', 'owner', 'viewer'])
def get_license_types():
    """Get all license types"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, icon_filename, created_at, updated_at
            FROM license_types
            ORDER BY name
        """)
        
        license_types = []
        for row in cursor.fetchall():
            license_types.append({
                "id": row[0],
                "name": row[1],
                "icon_url": get_icon_url(row[2]) if row[2] else None,
                "created_at": row[3],
                "updated_at": row[4]
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "license_types": license_types
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/license-types', methods=['POST'])
@login_required
@role_required(['admin', 'owner'])
def create_license_type():
    """Create a new license type with optional icon"""
    try:
        # Check if form data or JSON data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Form data with file upload
            name = request.form.get('name')
            icon_file = request.files.get('icon')
        else:
            # JSON data
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            name = data.get('name')
            icon_file = None
        
        if not name:
            return jsonify({
                "success": False,
                "error": "License type name is required"
            }), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if name already exists
        cursor.execute("SELECT id FROM license_types WHERE name = ?", (name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "error": "License type with this name already exists"
            }), 409
        
        # Handle icon upload
        icon_filename = None
        if icon_file and icon_file.filename:
            icon_filename = save_uploaded_file(icon_file)
            if not icon_filename:
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "Invalid file type. Allowed: jpg, jpeg, png, gif, svg, webp"
                }), 400
        
        # Create license type
        cursor.execute("""
            INSERT INTO license_types (name, icon_filename)
            VALUES (?, ?)
        """, (name, icon_filename))
        
        license_type_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event("create_license_type", session['username'], name, {
            "license_type_id": license_type_id,
            "icon_filename": icon_filename
        })
        
        return jsonify({
            "success": True,
            "message": "License type created successfully",
            "license_type": {
                "id": license_type_id,
                "name": name,
                "icon_url": get_icon_url(icon_filename) if icon_filename else None
            }
        }), 201
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/license-types/<int:license_type_id>', methods=['DELETE'])
@login_required
@role_required(['admin', 'owner'])
def delete_license_type(license_type_id):
    """Delete a license type and its icon file"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get license type info
        cursor.execute("""
            SELECT name, icon_filename FROM license_types WHERE id = ?
        """, (license_type_id,))
        
        license_type = cursor.fetchone()
        if not license_type:
            conn.close()
            return jsonify({
                "success": False,
                "error": "License type not found"
            }), 404
        
        name, icon_filename = license_type
        
        # Check if license type is in use
        cursor.execute("""
            SELECT COUNT(*) FROM licenses WHERE license_type_id = ?
        """, (license_type_id,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Cannot delete license type that is currently in use"
            }), 400
        
        # Delete license type
        cursor.execute("DELETE FROM license_types WHERE id = ?", (license_type_id,))
        conn.commit()
        conn.close()
        
        # Delete icon file if it exists
        if icon_filename:
            try:
                icon_path = UPLOAD_FOLDER / icon_filename
                if icon_path.exists():
                    icon_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete icon file {icon_filename}: {e}")
        
        # Log the action
        log_audit_event("delete_license_type", session['username'], name, {
            "license_type_id": license_type_id,
            "icon_filename": icon_filename
        })
        
        return jsonify({
            "success": True,
            "message": f"License type '{name}' deleted successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# STATIC FILE SERVING

@app.route('/static/icons/<filename>')
def serve_icon(filename):
    """Serve icon files"""
    return send_from_directory(UPLOAD_FOLDER, filename)


# AUDIT LOG ENDPOINTS

@app.route('/audit/logs', methods=['GET'])
@login_required
@role_required('owner')
def get_audit_logs():
    """Get audit logs (owner only)"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, action_type, performed_by, target, details
            FROM audit_log
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        logs = []
        for row in cursor.fetchall():
            details = json.loads(row[5]) if row[5] else None
            logs.append({
                "id": row[0],
                "timestamp": row[1],
                "action_type": row[2],
                "performed_by": row[3],
                "target": row[4],
                "details": details
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "logs": logs
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# MAIN APPLICATION ENDPOINTS (Protected)

@app.route('/')
@login_required
def home():
    """Root endpoint - shows API is running"""
    return jsonify({
        "message": "License Manager API is running",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "current_user": {
            "username": session['username'],
            "role": session['role']
        },
        "endpoints": {
            "auth": {
                "POST /login": "Login",
                "POST /logout": "Logout",
                "GET /auth/me": "Get current user",
                "GET /auth/admins": "List admins (owner only)",
                "POST /auth/admins": "Create admin/viewer (owner only)",
                "DELETE /auth/admins/<id>": "Delete admin/viewer (owner only)",
                "POST /auth/transfer-ownership": "Transfer ownership (owner only)",
                "POST /auth/reset-password": "Reset password (admin can reset viewers, owner can reset anyone)",
                "POST /auth/change-password": "Change own password (admin/owner only)"
            },
            "audit": {
                "GET /audit/logs": "Get audit logs (owner only)"
            },
            "users": {
                "GET /users": "List all users (admin/owner/viewer)",
                "GET /users/<id>": "Get single user (admin/owner/viewer)",
                "POST /users": "Create user (admin/owner only)",
                "PUT /users/<id>": "Update user (admin/owner only)",
                "DELETE /users/<id>": "Delete user (admin/owner only)"
            },
            "licenses": {
                "GET /licenses": "List all licenses (admin/owner/viewer)",
                "POST /licenses": "Assign license (admin/owner only)",
                "DELETE /licenses/<id>": "Revoke license (admin/owner only)"
            },
            "license_types": {
                "GET /license-types": "List all license types (admin/owner/viewer)",
                "POST /license-types": "Create license type (admin/owner only)",
                "DELETE /license-types/<id>": "Delete license type (admin/owner only)"
            }
        }
    })


# USER ENDPOINTS (Protected)

@app.route('/users', methods=['GET'])
@login_required
@role_required(['admin', 'owner', 'viewer'])
def get_users():
    """Get all users with their licenses"""
    try:
        users, licenses = get_users_with_licenses()
        formatted_users = format_user_data(users, licenses)
        
        # Log the action
        log_audit_event("view_users", session['username'])
        
        return jsonify({
            "success": True,
            "count": len(formatted_users),
            "users": formatted_users
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/users/<int:user_id>', methods=['GET'])
@login_required
@role_required(['admin', 'owner', 'viewer'])
def get_user(user_id):
    """Get details of a single user and their licenses"""
    try:
        user, licenses = get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "error": f"User with ID {user_id} not found"
            }), 404
        
        formatted_user = format_single_user(user, licenses)
        
        # Log the action
        log_audit_event("view_user", session['username'], f"user_id:{user_id}")
        
        return jsonify({
            "success": True,
            "user": formatted_user
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/users', methods=['POST'])
@login_required
@role_required(['admin', 'owner'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        name = data['name']
        email = data['email']
        department = data.get('department', '')
        manager = data.get('manager', '')
        title = data.get('title', '')
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "error": "User with this email already exists"
            }), 409
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (name, email, department, manager, title)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, department, manager, title))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Get the created user
        user, licenses = get_user_by_id(user_id)
        formatted_user = format_single_user(user, licenses)
        
        # Log the action
        log_audit_event("create_user", session['username'], email, {
            "user_id": user_id,
            "name": name,
            "department": department
        })
        
        return jsonify({
            "success": True,
            "message": "User created successfully",
            "user": formatted_user
        }), 201
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required(['admin', 'owner'])
def update_user(user_id):
    """Update an existing user's details"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Check if user exists
        user, _ = get_user_by_id(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": f"User with ID {user_id} not found"
            }), 404
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if 'name' in data:
            update_fields.append("name = ?")
            values.append(data['name'])
        
        if 'email' in data:
            # Check if email is being changed and if it already exists
            if data['email'] != user[2]:  # user[2] is email
                cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (data['email'], user_id))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({
                        "success": False,
                        "error": "User with this email already exists"
                    }), 409
            update_fields.append("email = ?")
            values.append(data['email'])
        
        if 'department' in data:
            update_fields.append("department = ?")
            values.append(data['department'])
        
        if 'manager' in data:
            update_fields.append("manager = ?")
            values.append(data['manager'])
        
        if 'title' in data:
            update_fields.append("title = ?")
            values.append(data['title'])
        
        if not update_fields:
            conn.close()
            return jsonify({
                "success": False,
                "error": "No valid fields to update"
            }), 400
        
        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        
        # Execute update
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        # Get updated user
        updated_user, licenses = get_user_by_id(user_id)
        formatted_user = format_single_user(updated_user, licenses)
        
        # Log the action
        log_audit_event("update_user", session['username'], f"user_id:{user_id}", {
            "updated_fields": list(data.keys()),
            "title_changed": "title" in data
        })
        
        return jsonify({
            "success": True,
            "message": "User updated successfully",
            "user": formatted_user
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required(['admin', 'owner'])
def delete_user(user_id):
    """Delete a user and any associated licenses"""
    try:
        # Check if user exists
        user, _ = get_user_by_id(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": f"User with ID {user_id} not found"
            }), 404
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Delete associated licenses first (due to foreign key constraint)
        cursor.execute("DELETE FROM licenses WHERE user_id = ?", (user_id,))
        licenses_deleted = cursor.rowcount
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event("delete_user", session['username'], f"user_id:{user_id}", {
            "user_email": user[2],
            "licenses_deleted": licenses_deleted
        })
        
        return jsonify({
            "success": True,
            "message": f"User and {licenses_deleted} associated licenses deleted successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# LICENSE ENDPOINTS (Protected)

@app.route('/licenses', methods=['GET'])
@login_required
@role_required(['admin', 'owner', 'viewer'])
def get_licenses():
    """List all licenses with user info"""
    try:
        licenses = get_all_licenses()
        formatted_licenses = format_license_data(licenses)
        
        # Log the action
        log_audit_event("view_licenses", session['username'])
        
        return jsonify({
            "success": True,
            "count": len(formatted_licenses),
            "licenses": formatted_licenses
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/licenses', methods=['POST'])
@login_required
@role_required(['admin', 'owner'])
def assign_license():
    """Assign a license to a user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Validate required fields
        required_fields = ['user_id', 'software_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        user_id = data['user_id']
        software_name = data['software_name']
        license_key = data.get('license_key', '')
        license_type = data.get('license_type', '')
        notes = data.get('notes', '')
        
        # Check if user exists
        user, _ = get_user_by_id(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": f"User with ID {user_id} not found"
            }), 404
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Insert new license
        cursor.execute("""
            INSERT INTO licenses (user_id, software_name, license_key, license_type, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, software_name, license_key, license_type, notes))
        
        license_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Get the created license with user info
        licenses = get_all_licenses()
        created_license = None
        for license_data in licenses:
            if license_data[0] == license_id:
                created_license = {
                    "id": license_data[0],
                    "user_id": license_data[1],
                    "user_name": license_data[2],
                    "user_email": license_data[3],
                    "software_name": license_data[4],
                    "license_key": license_data[5],
                    "license_type": license_data[6],
                    "status": license_data[7],
                    "assigned_date": license_data[8],
                    "revoked_date": license_data[9],
                    "notes": license_data[10]
                }
                break
        
        # Log the action
        log_audit_event("assign_license", session['username'], f"user_id:{user_id}", {
            "license_id": license_id,
            "software_name": software_name,
            "license_type": license_type
        })
        
        return jsonify({
            "success": True,
            "message": "License assigned successfully",
            "license": created_license
        }), 201
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/licenses/<int:license_id>', methods=['DELETE'])
@login_required
@role_required(['admin', 'owner'])
def revoke_license(license_id):
    """Revoke (delete) a license"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if license exists
        cursor.execute("""
            SELECT l.id, l.software_name, u.name as user_name, u.id as user_id
            FROM licenses l
            JOIN users u ON l.user_id = u.id
            WHERE l.id = ?
        """, (license_id,))
        
        license_data = cursor.fetchone()
        if not license_data:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"License with ID {license_id} not found"
            }), 404
        
        # Delete license
        cursor.execute("DELETE FROM licenses WHERE id = ?", (license_id,))
        
        conn.commit()
        conn.close()
        
        # Log the action
        log_audit_event("revoke_license", session['username'], f"license_id:{license_id}", {
            "software_name": license_data[1],
            "user_name": license_data[2],
            "user_id": license_data[3]
        })
        
        return jsonify({
            "success": True,
            "message": f"License '{license_data[1]}' for user '{license_data[2]}' revoked successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ERROR HANDLERS

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": {
            "auth": ["POST /login", "POST /logout", "GET /auth/me"],
            "users": ["GET /users", "GET /users/<id>", "POST /users", "PUT /users/<id>", "DELETE /users/<id>"],
            "licenses": ["GET /licenses", "POST /licenses", "DELETE /licenses/<id>"]
        }
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    print("🚀 Starting License Manager API with Authentication...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🔐 Authentication System:")
    print("   - POST /login (Login)")
    print("   - POST /logout (Logout)")
    print("   - GET /auth/me (Get current user)")
    print("   - POST /auth/change-password (Change own password - admin/owner only)")
    print("👑 Admin Management (Owner Only):")
    print("   - GET /auth/admins (List admins)")
    print("   - POST /auth/admins (Create admin/viewer)")
    print("   - DELETE /auth/admins/<id> (Delete admin/viewer)")
    print("   - POST /auth/transfer-ownership (Transfer ownership)")
    print("   - POST /auth/reset-password (Reset password - admin can reset viewers, owner can reset anyone)")
    print("📋 Audit Logging (Owner Only):")
    print("   - GET /audit/logs (View audit logs)")
    print("👥 User Management:")
    print("   - GET /users (List all users - admin/owner/viewer)")
    print("   - GET /users/<id> (Get single user - admin/owner/viewer)")
    print("   - POST /users (Create user - admin/owner only)")
    print("   - PUT /users/<id> (Update user - admin/owner only)")
    print("   - DELETE /users/<id> (Delete user - admin/owner only)")
    print("🔑 License Management:")
    print("   - GET /licenses (List all licenses - admin/owner/viewer)")
    print("   - POST /licenses (Assign license - admin/owner only)")
    print("   - DELETE /licenses/<id> (Revoke license - admin/owner only)")
    print("\n🎨 License Type Management:")
    print("   - GET /license-types (List all license types - admin/owner/viewer)")
    print("   - POST /license-types (Create license type with icon - admin/owner only)")
    print("   - DELETE /license-types/<id> (Delete license type - admin/owner only)")
    print("\n👁️  Viewer Role:")
    print("   - Can view users, licenses, and license types (read-only)")
    print("   - Cannot modify data, change passwords, or reset passwords")
    print("   - Cannot access admin functions or audit logs")
    print("\n🔑 Default Owner Account:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   ⚠️  Change this password immediately after first login!")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 