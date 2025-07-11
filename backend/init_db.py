#!/usr/bin/env python3
"""
Database initialization script for License Manager
Creates SQLite database with users, licenses, and license_types tables
"""

import sqlite3
import os
from pathlib import Path


def create_database():
    """Create the SQLite database and tables"""
    
    # Ensure db directory exists
    db_dir = Path("../db")
    db_dir.mkdir(exist_ok=True)
    
    # Ensure static/icons directory exists
    static_dir = Path("../static")
    static_dir.mkdir(exist_ok=True)
    icons_dir = static_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = db_dir / "license_manager.db"
    
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table with title field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT,
            manager TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create license_types table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS license_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create licenses table (will be updated to reference license_types)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            license_type_id INTEGER,
            software_name TEXT NOT NULL,
            license_key TEXT,
            license_type TEXT,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_date TIMESTAMP,
            status TEXT DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (license_type_id) REFERENCES license_types (id)
        )
    ''')
    
    # Insert some default license types
    default_license_types = [
        ("ChatGPT", "chatgpt.png"),
        ("GitHub Copilot", "github-copilot.png"),
        ("Visual Studio Code", "vscode.png"),
        ("Adobe Creative Suite", "adobe.png"),
        ("Microsoft Office", "office.png"),
        ("Slack", "slack.png"),
        ("Zoom", "zoom.png"),
        ("Notion", "notion.png")
    ]
    
    for name, icon in default_license_types:
        cursor.execute("""
            INSERT OR IGNORE INTO license_types (name, icon_filename)
            VALUES (?, ?)
        """, (name, icon))
    
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
        print(f"📊 Tables created: users, licenses, license_types")
        print(f"📁 Static directory: {Path('../static/icons').absolute()}")
        print(f"🎨 Default license types added")
        print("\n🎉 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 