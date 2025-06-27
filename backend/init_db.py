#!/usr/bin/env python3
"""
Database initialization script for License Manager
Creates SQLite database with users and licenses tables
"""

import sqlite3
import os
from pathlib import Path


def create_database():
    """Create the SQLite database and tables"""
    
    # Ensure db directory exists
    db_dir = Path("../db")
    db_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = db_dir / "license_manager.db"
    
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT,
            manager TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create licenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            software_name TEXT NOT NULL,
            license_key TEXT,
            license_type TEXT,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_date TIMESTAMP,
            status TEXT DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    return db_path


def main():
    """Main function to initialize the database"""
    try:
        print("🚀 Initializing License Manager Database...")
        
        # Create database and tables
        db_path = create_database()
        
        print(f"✅ Database created successfully!")
        print(f"📁 Database location: {db_path.absolute()}")
        print(f"📊 Tables created: users, licenses")
        print("\n🎉 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 