#!/usr/bin/env python3
"""
CRM Extended Features Backend API Testing Suite
Tests new extended features: reminders, statuses, archive/restore, export, activity log, manager stats, audio upload
"""

import requests
import sys
import json
from datetime import datetime, timedelta, timezone

class ExtendedCRMAPITester:
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
            'payments': [],
            'reminders': [],
            'statuses': []
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

    def test_create_test_client(self):
        """Create a test client for extended features testing"""
        client_data = {
            "name": "Extended Test Client",
            "phone": "+998901234567",
            "source": "Extended Test",
            "status": "new"
        }
        success, response = self.run_test("Create Test Client", "POST", "api/clients", 200, data=client_data)
        if success and response.get('id'):
            self.created_resources['clients'].append(response['id'])
            return True
        return False

    # REMINDER SYSTEM TESTS
    def test_create_reminder(self):
        """Test reminder creation"""
        if not self.created_resources['clients']:
            self.log("No clients to add reminders", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        reminder_data = {
            "client_id": client_id,
            "text": "Test reminder for client",
            "remind_at": future_time
        }
        success, response = self.run_test("Create Reminder", "POST", "api/reminders", 200, data=reminder_data)
        if success and response.get('id'):
            self.created_resources['reminders'].append(response['id'])
            return True
        return False

    def test_get_reminders(self):
        """Test get reminders"""
        success, response = self.run_test("Get Reminders", "GET", "api/reminders", 200)
        return success and isinstance(response, list)

    def test_get_overdue_reminders(self):
        """Test get overdue reminders"""
        success, response = self.run_test("Get Overdue Reminders", "GET", "api/reminders/overdue", 200)
        return success and isinstance(response, list)

    def test_update_reminder(self):
        """Test reminder update"""
        if not self.created_resources['reminders']:
            self.log("No reminders to update", False)
            return False
        
        reminder_id = self.created_resources['reminders'][0]
        update_data = {"is_completed": True}
        success, response = self.run_test("Update Reminder", "PUT", f"api/reminders/{reminder_id}", 200, data=update_data)
        return success and response.get('is_completed') == True

    # CUSTOM STATUS MANAGEMENT TESTS
    def test_get_statuses(self):
        """Test get statuses"""
        success, response = self.run_test("Get Statuses", "GET", "api/statuses", 200)
        return success and isinstance(response, list)

    def test_create_custom_status(self):
        """Test custom status creation"""
        status_data = {
            "name": "custom_test_status",
            "color": "#FF5722",
            "order": 10
        }
        success, response = self.run_test("Create Custom Status", "POST", "api/statuses", 200, data=status_data)
        if success and response.get('id'):
            self.created_resources['statuses'].append(response['id'])
            return True
        return False

    def test_update_status(self):
        """Test status update"""
        if not self.created_resources['statuses']:
            self.log("No custom statuses to update", False)
            return False
        
        status_id = self.created_resources['statuses'][0]
        update_data = {"color": "#4CAF50"}
        success, response = self.run_test("Update Status", "PUT", f"api/statuses/{status_id}", 200, data=update_data)
        return success and response.get('color') == '#4CAF50'

    # ARCHIVE/RESTORE TESTS
    def test_archive_client(self):
        """Test client archiving"""
        if not self.created_resources['clients']:
            self.log("No clients to archive", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        success, response = self.run_test("Archive Client", "POST", f"api/clients/{client_id}/archive", 200)
        return success

    def test_get_archived_clients(self):
        """Test get archived clients"""
        success, response = self.run_test("Get Archived Clients", "GET", "api/clients", 200, params={"is_archived": True})
        return success and isinstance(response, list)

    def test_restore_client(self):
        """Test client restoration"""
        if not self.created_resources['clients']:
            self.log("No clients to restore", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        success, response = self.run_test("Restore Client", "POST", f"api/clients/{client_id}/restore", 200)
        return success

    # EXPORT TESTS
    def test_export_clients_csv(self):
        """Test CSV export"""
        try:
            url = f"{self.base_url}/api/export/clients?format=csv"
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(url, headers=headers)
            
            self.tests_run += 1
            self.log("Testing Export Clients CSV...")
            
            if response.status_code == 200 and 'text/csv' in response.headers.get('content-type', ''):
                self.tests_passed += 1
                self.log("PASSED - CSV export working", True)
                return True
            else:
                self.log(f"FAILED - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}", False)
                return False
        except Exception as e:
            self.log(f"FAILED - Error: {str(e)}", False)
            return False

    # ACTIVITY LOG TESTS
    def test_get_activity_log(self):
        """Test activity log"""
        success, response = self.run_test("Get Activity Log", "GET", "api/activity-log", 200, params={"limit": 10})
        return success and isinstance(response, list)

    def test_filter_activity_log(self):
        """Test activity log filtering"""
        success, response = self.run_test("Filter Activity Log", "GET", "api/activity-log", 200, params={"entity_type": "client", "limit": 10})
        return success and isinstance(response, list)

    # MANAGER STATS TESTS
    def test_manager_stats(self):
        """Test manager statistics"""
        success, response = self.run_test("Get Manager Stats", "GET", "api/dashboard/manager-stats", 200)
        return success and isinstance(response, list)

    def test_recent_dashboard_data(self):
        """Test recent dashboard data"""
        success1, response1 = self.run_test("Get Recent Clients", "GET", "api/dashboard/recent-clients", 200)
        success2, response2 = self.run_test("Get Recent Notes", "GET", "api/dashboard/recent-notes", 200)
        return success1 and success2 and isinstance(response1, list) and isinstance(response2, list)

    # USD CURRENCY TESTS
    def test_usd_payment(self):
        """Test USD currency payment"""
        if not self.created_resources['clients']:
            self.log("No clients to add USD payments", False)
            return False
        
        client_id = self.created_resources['clients'][0]
        payment_data = {
            "client_id": client_id,
            "amount": 500.00,
            "currency": "USD",
            "status": "paid",
            "date": "2024-01-15"
        }
        success, response = self.run_test("Create USD Payment", "POST", "api/payments", 200, data=payment_data)
        if success and response.get('id'):
            self.created_resources['payments'].append(response['id'])
            return response.get('currency') == 'USD'
        return False

    def cleanup_resources(self):
        """Clean up created test resources"""
        self.log("Cleaning up extended test resources...")
        
        # Delete payments
        for payment_id in self.created_resources['payments']:
            self.run_test(f"Cleanup Payment {payment_id}", "DELETE", f"api/payments/{payment_id}", 200)
        
        # Delete reminders
        for reminder_id in self.created_resources['reminders']:
            self.run_test(f"Cleanup Reminder {reminder_id}", "DELETE", f"api/reminders/{reminder_id}", 200)
        
        # Delete custom statuses
        for status_id in self.created_resources['statuses']:
            self.run_test(f"Cleanup Status {status_id}", "DELETE", f"api/statuses/{status_id}", 200)
        
        # Delete clients
        for client_id in self.created_resources['clients']:
            self.run_test(f"Cleanup Client {client_id}", "DELETE", f"api/clients/{client_id}", 200)

    def run_all_tests(self):
        """Run complete extended test suite"""
        self.log("🚀 Starting CRM Extended Features Backend API Tests")
        self.log("=" * 60)
        
        # Login
        if not self.test_admin_login():
            self.log("Admin login failed - stopping tests", False)
            return False
        
        # Setup test data
        self.test_create_test_client()
        
        # Extended feature tests
        self.log("\n📝 Testing Reminder System...")
        self.test_create_reminder()
        self.test_get_reminders()
        self.test_get_overdue_reminders()
        self.test_update_reminder()
        
        self.log("\n🏷️ Testing Custom Status Management...")
        self.test_get_statuses()
        self.test_create_custom_status()
        self.test_update_status()
        
        self.log("\n📦 Testing Archive/Restore...")
        self.test_archive_client()
        self.test_get_archived_clients()
        self.test_restore_client()
        
        self.log("\n📊 Testing Export & Analytics...")
        self.test_export_clients_csv()
        self.test_manager_stats()
        self.test_recent_dashboard_data()
        
        self.log("\n📋 Testing Activity Log...")
        self.test_get_activity_log()
        self.test_filter_activity_log()
        
        self.log("\n💰 Testing USD Currency...")
        self.test_usd_payment()
        
        # Cleanup
        self.cleanup_resources()
        
        # Results
        self.log("=" * 60)
        self.log(f"📊 Extended Tests completed: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Success rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ExtendedCRMAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())