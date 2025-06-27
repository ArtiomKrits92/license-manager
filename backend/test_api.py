#!/usr/bin/env python3
"""
Simple test script to verify the API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_get_users():
    """Test getting all users"""
    print("🔍 Testing GET /users...")
    try:
        response = requests.get(f"{BASE_URL}/users")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['count']} users")
            for user in data['users']:
                print(f"   - {user['name']} ({user['email']}) - {len(user['licenses'])} licenses")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_user():
    """Test creating a new user"""
    print("\n🔍 Testing POST /users...")
    try:
        user_data = {
            "name": "API Test User",
            "email": "apitest@company.com",
            "department": "API Testing",
            "manager": "Test Manager"
        }
        
        response = requests.post(
            f"{BASE_URL}/users",
            headers={"Content-Type": "application/json"},
            data=json.dumps(user_data)
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Success! Created user: {data['user']['name']}")
            print(f"   User ID: {data['user']['id']}")
            return data['user']['id']
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_assign_license(user_id):
    """Test assigning a license to a user"""
    print(f"\n🔍 Testing POST /licenses for user {user_id}...")
    try:
        license_data = {
            "user_id": user_id,
            "software_name": "API Test Software",
            "license_type": "Test License",
            "notes": "Created via API test"
        }
        
        response = requests.post(
            f"{BASE_URL}/licenses",
            headers={"Content-Type": "application/json"},
            data=json.dumps(license_data)
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Success! Assigned license: {data['license']['software_name']}")
            return data['license']['id']
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_licenses():
    """Test getting all licenses"""
    print("\n🔍 Testing GET /licenses...")
    try:
        response = requests.get(f"{BASE_URL}/licenses")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['count']} licenses")
            for license_data in data['licenses']:
                print(f"   - {license_data['software_name']} -> {license_data['user_name']}")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🚀 Testing License Manager API...")
    print("=" * 50)
    
    # Test 1: Get all users
    test_get_users()
    
    # Test 2: Create a new user
    new_user_id = test_create_user()
    
    # Test 3: Assign a license to the new user
    if new_user_id:
        new_license_id = test_assign_license(new_user_id)
    
    # Test 4: Get all licenses
    test_get_licenses()
    
    # Test 5: Get all users again to see the new data
    print("\n" + "=" * 50)
    print("🔄 Checking updated user list...")
    test_get_users()
    
    print("\n✅ API testing complete!")

if __name__ == "__main__":
    main() 