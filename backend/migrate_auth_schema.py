#!/usr/bin/env python3
"""
Migration script to update auth_users table schema to include 'viewer' role
"""

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash


def migrate_auth_schema():
    """Migrate the auth_users table to include 'viewer' role"""
    
    # Database file path
    db_path = Path("../db/license_manager.db")
    
    if not db_path.exists():
        print("❌ Database file not found. Please run init_db.py first.")
        return False
    
    print("🔧 Migrating auth_users table schema...")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(auth_users)")
        columns = cursor.fetchall()
        
        # Find the role column
        role_column = None
        for col in columns:
            if col[1] == 'role':
                role_column = col
                break
        
        if not role_column:
            print("❌ auth_users table not found. Please run the Flask app first to create it.")
            conn.close()
            return False
        
        # Check if migration is needed
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='auth_users'")
        create_sql = cursor.fetchone()[0]
        
        if "'viewer'" in create_sql:
            print("✅ Schema already includes 'viewer' role. No migration needed.")
            conn.close()
            return True
        
        print("📋 Current schema doesn't include 'viewer' role. Migrating...")
        
        # Backup existing data
        cursor.execute("SELECT id, username, password_hash, role, created_at, updated_at FROM auth_users")
        existing_users = cursor.fetchall()
        
        print(f"📊 Found {len(existing_users)} existing users")
        
        # Drop the old table
        cursor.execute("DROP TABLE auth_users")
        
        # Create new table with updated schema
        cursor.execute('''
            CREATE TABLE auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'owner', 'viewer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Restore existing data
        for user in existing_users:
            user_id, username, password_hash, role, created_at, updated_at = user
            cursor.execute("""
                INSERT INTO auth_users (id, username, password_hash, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, password_hash, role, created_at, updated_at))
        
        # Ensure we have an owner account
        cursor.execute("SELECT COUNT(*) FROM auth_users WHERE role = 'owner'")
        owner_count = cursor.fetchone()[0]
        
        if owner_count == 0:
            print("👑 Creating default owner account...")
            initial_password = "admin123"
            password_hash = generate_password_hash(initial_password)
            cursor.execute("""
                INSERT INTO auth_users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, ("admin", password_hash, "owner"))
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        print(f"📊 Restored {len(existing_users)} users")
        print("🎯 'viewer' role is now supported")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def main():
    """Main function to run the migration"""
    print("🚀 Starting auth_users schema migration...")
    print("=" * 50)
    
    success = migrate_auth_schema()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Migration completed successfully!")
        print("🎉 You can now create 'viewer' users")
        print("=" * 50)
        return 0
    else:
        print("\n" + "=" * 50)
        print("❌ Migration failed!")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    exit(main()) 