#!/usr/bin/env python3
"""
Comprehensive test script for new license-manager features:
1. User info enhancement (title field)
2. License type management with icon uploads
3. Role-based access control
4. File upload and serving
5. Audit logging verification
"""

import requests
import json
import os
import tempfile
from pathlib import Path
from PIL import Image
import uuid

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class LicenseManagerTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_user_id = None
        self.test_license_type_id = None
        self.test_icon_filename = None
        
    def login_as_owner(self):
        """Login as owner and return success status"""
        print("🔐 Logging in as owner...")
        
        response = self.session.post(f"{BASE_URL}/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "Login response should be successful"
        assert data["user"]["role"] == "owner", "Should be logged in as owner"
        
        print("✅ Login successful as owner")
        return True
    
    def test_license_type_creation(self):
        """Test creating license types with and without icons"""
        print("\n🎨 Testing License Type Creation...")
        
        # Test 1: Create license type without icon
        license_type_data = {
            "name": "Test Software No Icon"
        }
        
        response = self.session.post(f"{BASE_URL}/license-types", json=license_type_data)
        assert response.status_code == 201, f"Failed to create license type: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "License type creation should be successful"
        assert data["license_type"]["name"] == "Test Software No Icon"
        assert data["license_type"]["icon_url"] is None, "Should have no icon URL"
        
        print("✅ License type created without icon")
        
        # Test 2: Create license type with icon
        # Create a temporary test image
        test_image_path = self.create_test_image()
        
        with open(test_image_path, 'rb') as f:
            files = {'icon': f}
            data = {'name': 'Test Software With Icon'}
            response = self.session.post(f"{BASE_URL}/license-types", files=files, data=data)
        
        assert response.status_code == 201, f"Failed to create license type with icon: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "License type creation with icon should be successful"
        assert data["license_type"]["name"] == "Test Software With Icon"
        assert data["license_type"]["icon_url"] is not None, "Should have icon URL"
        assert data["license_type"]["icon_url"].startswith("/static/icons/"), "Icon URL should be in static/icons/"
        
        # Store the license type ID and icon filename for later tests
        self.test_license_type_id = data["license_type"]["id"]
        self.test_icon_filename = data["license_type"]["icon_url"].split("/")[-1]
        
        print("✅ License type created with icon")
        
        # Clean up test image
        os.unlink(test_image_path)
        
        # Test 3: Verify icon file was saved
        icon_path = Path("../static/icons") / self.test_icon_filename
        assert icon_path.exists(), f"Icon file should exist at {icon_path}"
        assert icon_path.stat().st_size > 0, "Icon file should not be empty"
        
        print("✅ Icon file saved correctly")
        
        # Test 4: Verify icon can be served
        response = self.session.get(f"{BASE_URL}/static/icons/{self.test_icon_filename}")
        assert response.status_code == 200, "Icon should be served successfully"
        assert response.headers["content-type"].startswith("image/"), "Should serve image content type"
        
        print("✅ Icon serving works correctly")
    
    def create_test_image(self):
        """Create a temporary test image file"""
        # Create a simple test image
        img = Image.new('RGB', (64, 64), color='red')
        temp_path = tempfile.mktemp(suffix='.png')
        img.save(temp_path)
        return temp_path
    
    def test_user_creation_with_title(self):
        """Test creating a user with title and license assignment"""
        print("\n👤 Testing User Creation with Title...")
        
        # Create user with title
        user_data = {
            "name": "John Doe",
            "email": "john.doe@company.com",
            "department": "Engineering",
            "manager": "Jane Smith",
            "title": "Senior Software Engineer"
        }
        
        response = self.session.post(f"{BASE_URL}/users", json=user_data)
        assert response.status_code == 201, f"Failed to create user: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "User creation should be successful"
        assert data["user"]["name"] == "John Doe"
        assert data["user"]["title"] == "Senior Software Engineer"
        assert data["user"]["department"] == "Engineering"
        assert data["user"]["manager"] == "Jane Smith"
        
        self.test_user_id = data["user"]["id"]
        print("✅ User created with title")
        
        # Assign license to user
        license_data = {
            "user_id": self.test_user_id,
            "software_name": "Test Software With Icon",
            "license_type_id": self.test_license_type_id,
            "license_key": "TEST-KEY-123",
            "notes": "Test license assignment"
        }
        
        response = self.session.post(f"{BASE_URL}/licenses", json=license_data)
        assert response.status_code == 201, f"Failed to assign license: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "License assignment should be successful"
        
        print("✅ License assigned to user")
    
    def test_user_retrieval_with_enhanced_info(self):
        """Test retrieving user with enhanced information"""
        print("\n📋 Testing User Retrieval with Enhanced Info...")
        
        # Get specific user
        response = self.session.get(f"{BASE_URL}/users/{self.test_user_id}")
        assert response.status_code == 200, f"Failed to get user: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "User retrieval should be successful"
        
        user = data["user"]
        
        # Verify user fields
        assert user["name"] == "John Doe", "User name should match"
        assert user["email"] == "john.doe@company.com", "User email should match"
        assert user["department"] == "Engineering", "User department should match"
        assert user["manager"] == "Jane Smith", "User manager should match"
        assert user["title"] == "Senior Software Engineer", "User title should match"
        
        # Verify license information
        assert len(user["licenses"]) > 0, "User should have licenses"
        
        license_info = user["licenses"][0]
        assert license_info["software_name"] == "Test Software With Icon", "License software name should match"
        assert license_info["license_type_name"] == "Test Software With Icon", "License type name should match"
        assert license_info["icon_url"] is not None, "License should have icon URL"
        assert license_info["icon_url"].startswith("/static/icons/"), "Icon URL should be in static/icons/"
        
        print("✅ User retrieved with enhanced information")
        print(f"   Name: {user['name']}")
        print(f"   Title: {user['title']}")
        print(f"   Department: {user['department']}")
        print(f"   License: {license_info['software_name']}")
        print(f"   Icon: {license_info['icon_url']}")
    
    def test_viewer_access_control(self):
        """Test viewer role access control"""
        print("\n👁️ Testing Viewer Access Control...")
        
        # Create viewer account
        viewer_data = {
            "username": "test_viewer",
            "password": "password123",
            "role": "viewer"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/admins", json=viewer_data)
        assert response.status_code == 201, f"Failed to create viewer: {response.json()}"
        
        print("✅ Viewer account created")
        
        # Login as viewer
        viewer_session = requests.Session()
        response = viewer_session.post(f"{BASE_URL}/login", json={
            "username": "test_viewer",
            "password": "password123"
        })
        
        assert response.status_code == 200, f"Viewer login failed: {response.json()}"
        
        data = response.json()
        assert data["user"]["role"] == "viewer", "Should be logged in as viewer"
        
        print("✅ Viewer login successful")
        
        # Test allowed endpoints
        allowed_endpoints = [
            ("/users", "GET"),
            ("/users/1", "GET"),
            ("/license-types", "GET"),
            ("/licenses", "GET")
        ]
        
        for endpoint, method in allowed_endpoints:
            if method == "GET":
                response = viewer_session.get(f"{BASE_URL}{endpoint}")
            else:
                response = viewer_session.post(f"{BASE_URL}{endpoint}")
            
            assert response.status_code == 200, f"Viewer should be able to access {endpoint}"
            print(f"✅ Viewer can access {endpoint}")
        
        # Test blocked endpoints
        blocked_endpoints = [
            ("/users", "POST"),
            ("/users/1", "PUT"),
            ("/users/1", "DELETE"),
            ("/license-types", "POST"),
            ("/license-types/1", "DELETE"),
            ("/licenses", "POST"),
            ("/licenses/1", "DELETE"),
            ("/auth/change-password", "POST"),
            ("/audit/logs", "GET")
        ]
        
        for endpoint, method in blocked_endpoints:
            if method == "GET":
                response = viewer_session.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = viewer_session.post(f"{BASE_URL}{endpoint}", json={})
            elif method == "PUT":
                response = viewer_session.put(f"{BASE_URL}{endpoint}", json={})
            elif method == "DELETE":
                response = viewer_session.delete(f"{BASE_URL}{endpoint}")
            
            assert response.status_code == 403, f"Viewer should be blocked from {endpoint}, got {response.status_code}"
            print(f"✅ Viewer correctly blocked from {endpoint}")
    
    def test_audit_logging(self):
        """Test that audit logs were written for key actions"""
        print("\n📝 Testing Audit Logging...")
        
        # Get audit logs
        response = self.session.get(f"{BASE_URL}/audit/logs")
        assert response.status_code == 200, f"Failed to get audit logs: {response.json()}"
        
        data = response.json()
        assert data["success"] == True, "Audit log retrieval should be successful"
        
        logs = data["logs"]
        assert len(logs) > 0, "Should have audit logs"
        
        # Check for specific audit events
        audit_events = [
            "create_license_type",
            "create_user",
            "assign_license"
        ]
        
        found_events = []
        for log in logs:
            if log["action_type"] in audit_events:
                found_events.append(log["action_type"])
                print(f"✅ Found audit log: {log['action_type']} by {log['performed_by']}")
        
        # Verify we found the expected events
        for event in audit_events:
            assert event in found_events, f"Should have audit log for {event}"
        
        print("✅ All expected audit events logged")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test user (this will also delete associated licenses)
        if self.test_user_id:
            response = self.session.delete(f"{BASE_URL}/users/{self.test_user_id}")
            if response.status_code == 200:
                print("✅ Test user deleted")
        
        # Delete test license type
        if self.test_license_type_id:
            response = self.session.delete(f"{BASE_URL}/license-types/{self.test_license_type_id}")
            if response.status_code == 200:
                print("✅ Test license type deleted")
        
        # Delete test viewer
        response = self.session.delete(f"{BASE_URL}/auth/admins/2")  # Assuming viewer is ID 2
        if response.status_code == 200:
            print("✅ Test viewer deleted")
        
        # Verify icon file was deleted
        if self.test_icon_filename:
            icon_path = Path("../static/icons") / self.test_icon_filename
            assert not icon_path.exists(), f"Icon file should be deleted: {icon_path}"
            print("✅ Test icon file deleted")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive License Manager Tests")
        print("=" * 60)
        
        try:
            # Test 1: Login as owner
            self.login_as_owner()
            
            # Test 2: License type creation
            self.test_license_type_creation()
            
            # Test 3: User creation with title
            self.test_user_creation_with_title()
            
            # Test 4: User retrieval with enhanced info
            self.test_user_retrieval_with_enhanced_info()
            
            # Test 5: Viewer access control
            self.test_viewer_access_control()
            
            # Test 6: Audit logging
            self.test_audit_logging()
            
            # Cleanup
            self.cleanup_test_data()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED! ✅")
            print("=" * 60)
            print("\n✅ User title field enhancement works")
            print("✅ License type management with icons works")
            print("✅ File upload and serving works")
            print("✅ Role-based access control works")
            print("✅ Audit logging works")
            print("✅ All data cleanup successful")
            
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            return False
        except Exception as e:
            print(f"\n❌ UNEXPECTED ERROR: {e}")
            return False
        
        return True

def main():
    """Main test function"""
    tester = LicenseManagerTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n📋 Manual Testing Tips:")
        print("1. Test file upload: curl -X POST -F 'name=TestApp' -F 'icon=@/path/to/icon.png' http://localhost:5000/license-types")
        print("2. Test icon serving: http://localhost:5000/static/icons/filename.png")
        print("3. Check audit logs: GET /audit/logs (owner only)")
        print("4. Test viewer access: Login as viewer and try different endpoints")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main()) 