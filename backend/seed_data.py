import sqlite3

# Connect to the database
conn = sqlite3.connect("db/license_manager.db")
cursor = conn.cursor()

# Sample users
users = [
    ("Alice Smith", "alice@company.com", "Engineering", "Bob Manager"),
    ("David Chen", "david@company.com", "Marketing", "Sara Lead"),
    ("Liam Cohen", "liam@company.com", "IT", "Artiom Admin")
]

# Insert users
for name, email, dept, manager in users:
    cursor.execute("""
        INSERT OR IGNORE INTO users (name, email, department, manager)
        VALUES (?, ?, ?, ?)
    """, (name, email, dept, manager))

# Sample licenses
licenses = [
    (1, "GitHub Copilot", "XXXX-1234", "Seat-based"),
    (1, "ChatGPT Enterprise", None, "Usage-based"),
    (2, "Adobe Creative Cloud", "ADOBE-5678", "Named user"),
    (3, "Microsoft 365", "MS365-9988", "Subscription")
]

# Insert licenses
for user_id, software, key, ltype in licenses:
    cursor.execute("""
        INSERT INTO licenses (user_id, software_name, license_key, license_type)
        VALUES (?, ?, ?, ?)
    """, (user_id, software, key, ltype))
    print(f"✔️ License '{software}' added for user_id {user_id}")

conn.commit()
conn.close()

print("✅ Sample data inserted.")
