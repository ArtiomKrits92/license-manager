#!/usr/bin/env python3
"""
Flask API for License Manager
Provides complete CRUD endpoints for users and licenses
"""

from flask import Flask, jsonify, request
import sqlite3
from pathlib import Path
from datetime import datetime


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


def get_users_with_licenses():
    """Retrieve all users and their licenses from the database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("""
        SELECT id, name, email, department, manager, created_at, updated_at
        FROM users
        ORDER BY name
    """)
    users = cursor.fetchall()
    
    # Get all licenses with user information
    cursor.execute("""
        SELECT l.id, l.user_id, l.software_name, l.license_key, 
               l.license_type, l.status, l.assigned_date, l.revoked_date, l.notes
        FROM licenses l
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
        SELECT id, name, email, department, manager, created_at, updated_at
        FROM users
        WHERE id = ?
    """, (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return None, []
    
    # Get user's licenses
    cursor.execute("""
        SELECT id, user_id, software_name, license_key, 
               license_type, status, assigned_date, revoked_date, notes
        FROM licenses
        WHERE user_id = ?
        ORDER BY software_name
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
            "notes": license_data[8]
        }
        user_licenses[user_id].append(license_dict)
    
    # Format user data
    formatted_users = []
    for user in users:
        user_id, name, email, department, manager, created_at, updated_at = user
        
        user_dict = {
            "id": user_id,
            "name": name,
            "email": email,
            "department": department,
            "manager": manager,
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
    
    user_id, name, email, department, manager, created_at, updated_at = user
    
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
            "notes": license_data[8]
        }
        formatted_licenses.append(license_dict)
    
    return {
        "id": user_id,
        "name": name,
        "email": email,
        "department": department,
        "manager": manager,
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
               l.revoked_date, l.notes
        FROM licenses l
        JOIN users u ON l.user_id = u.id
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
            "notes": license_data[10]
        }
        formatted_licenses.append(license_dict)
    
    return formatted_licenses


# Initialize Flask app
app = Flask(__name__)


@app.route('/')
def home():
    """Root endpoint - shows API is running"""
    return jsonify({
        "message": "License Manager API is running",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "users": {
                "GET /users": "List all users",
                "GET /users/<id>": "Get single user",
                "POST /users": "Create user",
                "PUT /users/<id>": "Update user",
                "DELETE /users/<id>": "Delete user"
            },
            "licenses": {
                "GET /licenses": "List all licenses",
                "POST /licenses": "Assign license",
                "DELETE /licenses/<id>": "Revoke license"
            }
        }
    })


# USER ENDPOINTS

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users with their licenses"""
    try:
        users, licenses = get_users_with_licenses()
        formatted_users = format_user_data(users, licenses)
        
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
            INSERT INTO users (name, email, department, manager)
            VALUES (?, ?, ?, ?)
        """, (name, email, department, manager))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Get the created user
        user, licenses = get_user_by_id(user_id)
        formatted_user = format_single_user(user, licenses)
        
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
        
        return jsonify({
            "success": True,
            "message": f"User and {licenses_deleted} associated licenses deleted successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# LICENSE ENDPOINTS

@app.route('/licenses', methods=['GET'])
def get_licenses():
    """List all licenses with user info"""
    try:
        licenses = get_all_licenses()
        formatted_licenses = format_license_data(licenses)
        
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
def revoke_license(license_id):
    """Revoke (delete) a license"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if license exists
        cursor.execute("""
            SELECT l.id, l.software_name, u.name as user_name
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
        
        return jsonify({
            "success": True,
            "message": f"License '{license_data[1]}' for user '{license_data[2]}' revoked successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": {
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
    print("🚀 Starting License Manager API...")
    print("📡 Server will be available at: http://localhost:5000")
    print("📋 Available endpoints:")
    print("   USERS:")
    print("   - GET /users (List all users)")
    print("   - GET /users/<id> (Get single user)")
    print("   - POST /users (Create user)")
    print("   - PUT /users/<id> (Update user)")
    print("   - DELETE /users/<id> (Delete user)")
    print("   LICENSES:")
    print("   - GET /licenses (List all licenses)")
    print("   - POST /licenses (Assign license)")
    print("   - DELETE /licenses/<id> (Revoke license)")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 