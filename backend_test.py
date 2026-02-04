#!/usr/bin/env python3
"""
CRM Backend API Testing Suite
Tests all endpoints with admin credentials and comprehensive scenarios
"""

import requests
import sys
import json
from datetime import datetime

class CRMAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.token = None
        self.admin_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'clients': [],
            'users': [],
            'notes': [],
            'payments': []
        }

    def log(self, message, success=None):
        """Log test results with color coding"""
        if success is True:
            print(f"✅ {message}")
        elif success is False:
            print(f"❌ {message}")
        else:
            print(f"🔍 {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"PASSED - Status: {response.status_code}", True)
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"FAILED - Expected {expected_status}, got {response.status_code}", False)
                try:
                    error_detail = response.json()
                    self.log(f"Error details: {error_detail}")
                except:
                    self.log(f"Response text: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"FAILED - Error: {str(e)}", False)
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test("Health Check", "GET", "api/health", 200)
        return success and response.get('status') == 'healthy'

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/auth/login",
            200,
            data={"email": "admin@crm.local", "password": "admin123"}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.admin_user = response['user']
            self.log(f"Admin logged in: {self.admin_user['name']}")
            return True
        return False

    def test_get_profile(self):
        """Test get current user profile"""
        success, response = self.run_test("Get Profile", "GET", "api/auth/me", 200)
        return success and response.get('email') == 'admin@crm.local'

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test("Dashboard Stats", "GET", "api/dashboard/stats", 200)
        required_fields = ['total_clients', 'todays_leads', 'new_count', 'contacted_count', 'sold_count', 'total_paid', 'total_pending']
        if success:
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log(f"Missing dashboard fields: {missing_fields}", False)
                return False
            return True
        return False

    def test_create_client(self):
        """Test client creation"""
        client_data = {
            "name": "Test Client",
            "phone": "+998901234567",
            "source": "Test Source",
            "status": "new"
        }
        success, response = self.run_test("Create Client", "POST", "api/clients", 200, data=client_data)
        if success and response.get('id'):
            self.created_resources['clients'].append(response['id'])
            return True
        return False

    def test_get_clients(self):
        """Test get clients list"""
        success, response = self.run_test("Get Clients", "GET", "api/clients", 200)
        return success and isinstance(response, list)

    def test_search_clients(self):
        """Test client search functionality"""
        success, response = self.run_test(
            "Search Clients", 
            "GET", 
            "api/clients", 
            200, 
            params={"search": "Test"}
        )
        return success

    def test_filter_clients_by_status(self):
        """Test client filtering by status"""
        success, response = self.run_test(
            "Filter Clients by Status", 
            "GET", 
            "api/clients", 
            200, 
            params={"status": "new"}
        )
        return success

    def test_update_client(self):
        """Test client update"""
        if not self.created_resources['clients']:
            self.log("No clients to update", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        update_data = {"status": "contacted"}
        success, response = self.run_test(
            "Update Client Status", 
            "PUT", 
            f"api/clients/{client_id}", 
            200, 
            data=update_data
        )
        return success and response.get('status') == 'contacted'

    def test_get_client_detail(self):
        """Test get single client"""
        if not self.created_resources['clients']:
            self.log("No clients to get details", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        success, response = self.run_test("Get Client Detail", "GET", f"api/clients/{client_id}", 200)
        return success and response.get('id') == client_id

    def test_create_note(self):
        """Test note creation"""
        if not self.created_resources['clients']:
            self.log("No clients to add notes", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        note_data = {"client_id": client_id, "text": "Test note for client"}
        success, response = self.run_test("Create Note", "POST", "api/notes", 201, data=note_data)
        if success and response.get('id'):
            self.created_resources['notes'].append(response['id'])
            return True
        return False

    def test_get_notes(self):
        """Test get notes for client"""
        if not self.created_resources['clients']:
            self.log("No clients to get notes", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        success, response = self.run_test("Get Client Notes", "GET", f"api/notes/{client_id}", 200)
        return success and isinstance(response, list)

    def test_delete_note(self):
        """Test note deletion"""
        if not self.created_resources['notes']:
            self.log("No notes to delete", False)
            return False
        
        note_id = self.created_resources['notes'][0]
        success, response = self.run_test("Delete Note", "DELETE", f"api/notes/{note_id}", 200)
        if success:
            self.created_resources['notes'].remove(note_id)
        return success

    def test_create_payment(self):
        """Test payment creation"""
        if not self.created_resources['clients']:
            self.log("No clients to add payments", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        payment_data = {
            "client_id": client_id,
            "amount": 1000000,
            "status": "pending",
            "date": "2024-01-15"
        }
        success, response = self.run_test("Create Payment", "POST", "api/payments", 201, data=payment_data)
        if success and response.get('id'):
            self.created_resources['payments'].append(response['id'])
            return True
        return False

    def test_get_all_payments(self):
        """Test get all payments"""
        success, response = self.run_test("Get All Payments", "GET", "api/payments", 200)
        return success and isinstance(response, list)

    def test_get_client_payments(self):
        """Test get payments for specific client"""
        if not self.created_resources['clients']:
            self.log("No clients to get payments", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        success, response = self.run_test("Get Client Payments", "GET", f"api/payments/client/{client_id}", 200)
        return success and isinstance(response, list)

    def test_create_user(self):
        """Test user creation (admin only)"""
        user_data = {
            "name": "Test Manager",
            "email": "test.manager@crm.local",
            "phone": "+998901111111",
            "password": "testpass123",
            "role": "manager"
        }
        success, response = self.run_test("Create User", "POST", "api/users", 201, data=user_data)
        if success and response.get('id'):
            self.created_resources['users'].append(response['id'])
            return True
        return False

    def test_get_users(self):
        """Test get users list (admin only)"""
        success, response = self.run_test("Get Users", "GET", "api/users", 200)
        return success and isinstance(response, list)

    def test_update_user(self):
        """Test user update"""
        if not self.created_resources['users']:
            self.log("No users to update", False)
            return False
        
        user_id = self.created_resources['users'][0]
        update_data = {"name": "Updated Manager Name"}
        success, response = self.run_test("Update User", "PUT", f"api/users/{user_id}", 200, data=update_data)
        return success and response.get('name') == 'Updated Manager Name'

    def test_update_profile(self):
        """Test profile update"""
        update_data = {"name": "Updated Admin Name"}
        success, response = self.run_test("Update Profile", "PUT", "api/auth/profile", 200, data=update_data)
        return success

    def cleanup_resources(self):
        """Clean up created test resources"""
        self.log("Cleaning up test resources...")
        
        # Delete payments
        for payment_id in self.created_resources['payments']:
            self.run_test(f"Cleanup Payment {payment_id}", "DELETE", f"api/payments/{payment_id}", 200)
        
        # Delete notes
        for note_id in self.created_resources['notes']:
            self.run_test(f"Cleanup Note {note_id}", "DELETE", f"api/notes/{note_id}", 200)
        
        # Delete clients
        for client_id in self.created_resources['clients']:
            self.run_test(f"Cleanup Client {client_id}", "DELETE", f"api/clients/{client_id}", 200)
        
        # Delete users
        for user_id in self.created_resources['users']:
            self.run_test(f"Cleanup User {user_id}", "DELETE", f"api/users/{user_id}", 200)

    def run_all_tests(self):
        """Run complete test suite"""
        self.log("🚀 Starting CRM Backend API Tests")
        self.log("=" * 50)
        
        # Basic tests
        if not self.test_health_check():
            self.log("Health check failed - stopping tests", False)
            return False
        
        if not self.test_admin_login():
            self.log("Admin login failed - stopping tests", False)
            return False
        
        # Authentication tests
        self.test_get_profile()
        
        # Dashboard tests
        self.test_dashboard_stats()
        
        # Client management tests
        self.test_create_client()
        self.test_get_clients()
        self.test_search_clients()
        self.test_filter_clients_by_status()
        self.test_update_client()
        self.test_get_client_detail()
        
        # Notes tests
        self.test_create_note()
        self.test_get_notes()
        self.test_delete_note()
        
        # Payment tests
        self.test_create_payment()
        self.test_get_all_payments()
        self.test_get_client_payments()
        
        # User management tests (admin only)
        self.test_create_user()
        self.test_get_users()
        self.test_update_user()
        
        # Profile tests
        self.test_update_profile()
        
        # Cleanup
        self.cleanup_resources()
        
        # Results
        self.log("=" * 50)
        self.log(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Success rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = CRMAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())