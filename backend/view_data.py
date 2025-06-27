#!/usr/bin/env python3
"""
Data viewer script for License Manager
Displays all users and their assigned licenses
"""

import sqlite3
from pathlib import Path


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
    # (this will help identify the correct path)
    for db_path in possible_paths:
        try:
            return sqlite3.connect(db_path)
        except:
            continue
    
    raise FileNotFoundError("Could not find license_manager.db in any expected location")


def get_all_users_and_licenses():
    """Retrieve all users and their licenses from the database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("""
        SELECT id, name, email, department, manager
        FROM users
        ORDER BY name
    """)
    users = cursor.fetchall()
    
    # Get all licenses with user information
    cursor.execute("""
        SELECT l.id, l.user_id, u.name as user_name, l.software_name, 
               l.license_key, l.license_type, l.status, l.assigned_date
        FROM licenses l
        JOIN users u ON l.user_id = u.id
        ORDER BY u.name, l.software_name
    """)
    licenses = cursor.fetchall()
    
    conn.close()
    return users, licenses


def display_users_and_licenses():
    """Display all users and their licenses in a formatted way"""
    try:
        print("🔍 License Manager - Data Viewer")
        print("=" * 50)
        
        users, licenses = get_all_users_and_licenses()
        
        if not users:
            print("❌ No users found in the database.")
            return
        
        # Group licenses by user
        user_licenses = {}
        for license_data in licenses:
            user_id = license_data[1]
            if user_id not in user_licenses:
                user_licenses[user_id] = []
            user_licenses[user_id].append(license_data)
        
        # Display each user and their licenses
        for user in users:
            user_id, name, email, department, manager = user
            
            print(f"\n👤 USER: {name}")
            print(f"   📧 Email: {email}")
            print(f"   🏢 Department: {department}")
            print(f"   👨‍💼 Manager: {manager}")
            
            if user_id in user_licenses:
                print(f"   📋 Licenses ({len(user_licenses[user_id])}):")
                for license_data in user_licenses[user_id]:
                    _, _, _, software, key, ltype, status, assigned_date = license_data
                    print(f"      • {software}")
                    print(f"        Type: {ltype}")
                    if key:
                        print(f"        Key: {key}")
                    print(f"        Status: {status}")
                    print(f"        Assigned: {assigned_date}")
                    print()
            else:
                print("   📋 No licenses assigned")
            
            print("-" * 50)
        
        # Summary
        total_users = len(users)
        total_licenses = len(licenses)
        print(f"\n📊 SUMMARY:")
        print(f"   Total Users: {total_users}")
        print(f"   Total Licenses: {total_licenses}")
        
    except Exception as e:
        print(f"❌ Error viewing data: {e}")


def main():
    """Main function"""
    display_users_and_licenses()


if __name__ == "__main__":
    main() 