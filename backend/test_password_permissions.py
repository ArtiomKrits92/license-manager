#!/usr/bin/env python3
"""
Test script for password reset and change permissions in License Manager
Tests all roles (owner, admin, viewer) and their password-related capabilities
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

class PasswordPermissionTester:
    def __init__(self):
        self.owner_session = requests.Session()
        self.admin_session = requests.Session()
        self.viewer_session = requests.Session()
        self.test_users = []
        
    def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Generate unique usernames
        import time
        timestamp = int(time.time())
        self.admin_username = f"test_admin_{timestamp}"
        self.viewer_username = f"test_viewer_{timestamp}"
        
        # Login as owner
        response = self.owner_session.post(f"{BASE_URL}/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Owner login failed: {response.status_code}"
        print("✅ Owner logged in successfully")
        
        # Create test admin user with unique username
        admin_data = {
            "username": self.admin_username,
            "password": "admin123",
            "role": "admin"
        }
        response = self.owner_session.post(f"{BASE_URL}/auth/admins", json=admin_data)
        assert response.status_code == 201, f"Failed to create test admin: {response.status_code}"
        self.test_users.append((self.admin_username, "admin"))
        print("✅ Test admin created")
        
        # Create test viewer user with unique username
        viewer_data = {
            "username": self.viewer_username,
            "password": "viewer123",
            "role": "viewer"
        }
        response = self.owner_session.post(f"{BASE_URL}/auth/admins", json=viewer_data)
        assert response.status_code == 201, f"Failed to create test viewer: {response.status_code}"
        self.test_users.append((self.viewer_username, "viewer"))
        print("✅ Test viewer created")
        
        # Login as test admin
        response = self.admin_session.post(f"{BASE_URL}/login", json={
            "username": self.admin_username,
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        print("✅ Test admin logged in successfully")
        
        # Login as test viewer
        response = self.viewer_session.post(f"{BASE_URL}/login", json={
            "username": self.viewer_username,
            "password": "viewer123"
        })
        assert response.status_code == 200, f"Viewer login failed: {response.status_code}"
        print("✅ Test viewer logged in successfully")
        
    def test_admin_password_permissions(self):
        """Test admin password permissions"""
        print("\n🔐 Testing Admin Password Permissions...")
        
        # 1. Admin can change their own password
        print("Testing: Admin can change their own password")
        response = self.admin_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "admin123",
            "new_password": "newadmin123"
        })
        assert response.status_code == 200, f"Admin should be able to change own password, got {response.status_code}"
        print("✅ Admin can change their own password")
        
        # Verify the password change worked by logging in again
        response = self.admin_session.post(f"{BASE_URL}/login", json={
            "username": self.admin_username,
            "password": "newadmin123"
        })
        assert response.status_code == 200, "Admin should be able to login with new password"
        
        # Change password back for cleanup
        response = self.admin_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "newadmin123",
            "new_password": "admin123"
        })
        assert response.status_code == 200, "Admin should be able to change password back"
        
        # 2. Admin cannot reset another admin's password (should be 403)
        print("Testing: Admin cannot reset another admin's password")
        response = self.admin_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "admin",
            "new_password": "newpassword123"
        })
        assert response.status_code == 403, f"Admin should be blocked from resetting admin password, got {response.status_code}"
        print("✅ Admin correctly blocked from resetting admin password")
        
        # 3. Admin cannot reset the owner's password (should be 403)
        print("Testing: Admin cannot reset owner's password")
        response = self.admin_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "admin",
            "new_password": "newpassword123"
        })
        assert response.status_code == 403, f"Admin should be blocked from resetting owner password, got {response.status_code}"
        print("✅ Admin correctly blocked from resetting owner password")
        
        # 4. Admin can reset viewer password
        print("Testing: Admin can reset viewer password")
        response = self.admin_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.viewer_username,
            "new_password": "newviewer123"
        })
        assert response.status_code == 200, f"Admin should be able to reset viewer password, got {response.status_code}"
        print("✅ Admin can reset viewer password")
        
        # Verify the password reset worked
        response = self.viewer_session.post(f"{BASE_URL}/login", json={
            "username": self.viewer_username,
            "password": "newviewer123"
        })
        assert response.status_code == 200, "Viewer should be able to login with reset password"
        
        # Reset viewer password back
        response = self.admin_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.viewer_username,
            "new_password": "viewer123"
        })
        assert response.status_code == 200, "Admin should be able to reset viewer password back"
        
    def test_owner_password_permissions(self):
        """Test owner password permissions"""
        print("\n👑 Testing Owner Password Permissions...")
        
        # 1. Owner can change their own password
        print("Testing: Owner can change their own password")
        response = self.owner_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "admin123",
            "new_password": "newowner123"
        })
        assert response.status_code == 200, f"Owner should be able to change own password, got {response.status_code}"
        print("✅ Owner can change their own password")
        
        # Verify the password change worked by logging in again
        response = self.owner_session.post(f"{BASE_URL}/login", json={
            "username": "admin",
            "password": "newowner123"
        })
        assert response.status_code == 200, "Owner should be able to login with new password"
        
        # Change password back for cleanup
        response = self.owner_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "newowner123",
            "new_password": "admin123"
        })
        assert response.status_code == 200, "Owner should be able to change password back"
        
        # 2. Owner can reset admin's password
        print("Testing: Owner can reset admin's password")
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.admin_username,
            "new_password": "newadmin123"
        })
        assert response.status_code == 200, f"Owner should be able to reset admin password, got {response.status_code}"
        print("✅ Owner can reset admin's password")
        
        # Verify the password reset worked
        response = self.admin_session.post(f"{BASE_URL}/login", json={
            "username": self.admin_username,
            "password": "newadmin123"
        })
        assert response.status_code == 200, "Admin should be able to login with reset password"
        
        # Reset admin password back
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.admin_username,
            "new_password": "admin123"
        })
        assert response.status_code == 200, "Owner should be able to reset admin password back"
        
        # 3. Owner can reset viewer's password
        print("Testing: Owner can reset viewer's password")
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.viewer_username,
            "new_password": "newviewer123"
        })
        assert response.status_code == 200, f"Owner should be able to reset viewer password, got {response.status_code}"
        print("✅ Owner can reset viewer's password")
        
        # Verify the password reset worked
        response = self.viewer_session.post(f"{BASE_URL}/login", json={
            "username": self.viewer_username,
            "password": "newviewer123"
        })
        assert response.status_code == 200, "Viewer should be able to login with reset password"
        
        # Reset viewer password back
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.viewer_username,
            "new_password": "viewer123"
        })
        assert response.status_code == 200, "Owner should be able to reset viewer password back"
        
        # 4. Owner can reset their own password
        print("Testing: Owner can reset their own password")
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "admin",
            "new_password": "newowner123"
        })
        assert response.status_code == 200, f"Owner should be able to reset own password, got {response.status_code}"
        print("✅ Owner can reset their own password")
        
        # Verify and reset back
        response = self.owner_session.post(f"{BASE_URL}/login", json={
            "username": "admin",
            "password": "newowner123"
        })
        assert response.status_code == 200, "Owner should be able to login with reset password"
        
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "admin",
            "new_password": "admin123"
        })
        assert response.status_code == 200, "Owner should be able to reset own password back"
        
    def test_viewer_password_permissions(self):
        """Test viewer password permissions"""
        print("\n👁️ Testing Viewer Password Permissions...")
        
        # 1. Viewer cannot change their password (should be 403)
        print("Testing: Viewer cannot change their password")
        response = self.viewer_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "viewer123",
            "new_password": "newviewer123"
        })
        assert response.status_code == 403, f"Viewer should be blocked from changing password, got {response.status_code}"
        print("✅ Viewer correctly blocked from changing password")
        
        # 2. Viewer cannot reset anyone's password (should be 403)
        print("Testing: Viewer cannot reset anyone's password")
        response = self.viewer_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.viewer_username,
            "new_password": "newviewer123"
        })
        assert response.status_code == 403, f"Viewer should be blocked from resetting password, got {response.status_code}"
        print("✅ Viewer correctly blocked from resetting password")
        
        # Test resetting admin password
        response = self.viewer_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": self.admin_username,
            "new_password": "newadmin123"
        })
        assert response.status_code == 403, f"Viewer should be blocked from resetting admin password, got {response.status_code}"
        print("✅ Viewer correctly blocked from resetting admin password")
        
        # Test resetting owner password
        response = self.viewer_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "admin",
            "new_password": "newowner123"
        })
        assert response.status_code == 403, f"Viewer should be blocked from resetting owner password, got {response.status_code}"
        print("✅ Viewer correctly blocked from resetting owner password")
        
    def test_invalid_password_operations(self):
        """Test invalid password operations"""
        print("\n❌ Testing Invalid Password Operations...")
        
        # Test with invalid current password
        print("Testing: Change password with invalid current password")
        response = self.admin_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        })
        assert response.status_code == 401, f"Should get 401 for wrong current password, got {response.status_code}"
        print("✅ Correctly rejected change with wrong current password")
        
        # Test reset password for non-existent user
        print("Testing: Reset password for non-existent user")
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "nonexistent_user",
            "new_password": "newpassword123"
        })
        assert response.status_code == 404, f"Should get 404 for non-existent user, got {response.status_code}"
        print("✅ Correctly rejected reset for non-existent user")
        
        # Test missing required fields
        print("Testing: Change password with missing fields")
        response = self.admin_session.post(f"{BASE_URL}/auth/change-password", json={
            "current_password": "admin123"
            # Missing new_password
        })
        assert response.status_code == 400, f"Should get 400 for missing fields, got {response.status_code}"
        print("✅ Correctly rejected change with missing fields")
        
        # Test reset password with missing fields
        print("Testing: Reset password with missing fields")
        response = self.owner_session.post(f"{BASE_URL}/auth/reset-password", json={
            "username": "test_admin"
            # Missing new_password
        })
        assert response.status_code == 400, f"Should get 400 for missing fields, got {response.status_code}"
        print("✅ Correctly rejected reset with missing fields")
        
    def cleanup(self):
        """Clean up test users"""
        print("\n🧹 Cleaning up test users...")
        
        # Get list of admins to find test users
        response = self.owner_session.get(f"{BASE_URL}/auth/admins")
        assert response.status_code == 200, f"Failed to get admins list: {response.status_code}"
        
        admins = response.json().get("admins", [])
        for admin in admins:
            if admin["username"] in [self.admin_username, self.viewer_username]:
                response = self.owner_session.delete(f"{BASE_URL}/auth/admins/{admin['id']}")
                if response.status_code == 200:
                    print(f"✅ Deleted test user: {admin['username']}")
                else:
                    print(f"⚠️ Failed to delete test user: {admin['username']}")
        
        print("✅ Cleanup completed")
        
    def run_all_tests(self):
        """Run all password permission tests"""
        print("🚀 Starting Password Permission Tests")
        print("=" * 50)
        
        try:
            self.setup()
            self.test_admin_password_permissions()
            self.test_owner_password_permissions()
            self.test_viewer_password_permissions()
            self.test_invalid_password_operations()
            self.cleanup()
            
            print("\n" + "=" * 50)
            print("✅ All password permission tests passed")
            print("=" * 50)
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            print("=" * 50)
            raise

if __name__ == "__main__":
    tester = PasswordPermissionTester()
    tester.run_all_tests() 