"""
SchoolCRM Supabase Migration Tests
==================================
Tests for verifying the MongoDB to Supabase PostgreSQL migration.
Tests all CRUD operations for: users, clients, payments, reminders, notes, statuses, groups, tariffs, settings, activity_log
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://edusync-app-3.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@crm.local"
ADMIN_PASSWORD = "admin123"


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        # Verify UUID format (Supabase uses UUIDs)
        assert "-" in data["user"]["id"]  # UUID contains dashes
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_get_me_authenticated(self):
        """Test /api/auth/me with valid token"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Get current user
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
    
    def test_get_me_unauthenticated(self):
        """Test /api/auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]


class TestDashboardEndpoints:
    """Dashboard endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Verify expected fields
        assert "total_clients" in data
        assert "todays_leads" in data
        assert "sold_count" in data
        assert "total_paid" in data
        assert "new_count" in data
        assert "contacted_count" in data
    
    def test_dashboard_recent_clients(self):
        """Test recent clients endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-clients", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_dashboard_recent_notes(self):
        """Test recent notes endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-notes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_dashboard_manager_stats(self):
        """Test manager stats endpoint (admin only)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/manager-stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_dashboard_analytics(self):
        """Test analytics endpoint (admin only)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "monthly_data" in data or "summary" in data or isinstance(data, dict)


class TestClientsEndpoints:
    """Clients CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_clients_list(self):
        """Test getting clients list"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify migrated clients exist
        assert len(data) > 0, "Expected migrated clients to exist"
    
    def test_create_client(self):
        """Test creating a new client"""
        client_data = {
            "name": "TEST_Supabase Client",
            "phone": "+998901234567",
            "source": "Test",
            "status": "new"
        }
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == client_data["name"]
        assert data["phone"] == client_data["phone"]
        assert "id" in data
        # UUID format check
        assert "-" in data["id"]
        
        # Store for cleanup
        self.created_client_id = data["id"]
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/clients/{data['id']}", headers=self.headers)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == client_data["name"]
    
    def test_get_client_by_id(self):
        """Test getting a specific client"""
        # First get list to find a client
        list_response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        clients = list_response.json()
        if clients:
            client_id = clients[0]["id"]
            response = requests.get(f"{BASE_URL}/api/clients/{client_id}", headers=self.headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == client_id
    
    def test_update_client_status(self):
        """Test updating client status"""
        # Create a test client first
        client_data = {
            "name": "TEST_Status Update Client",
            "phone": "+998901234568",
            "status": "new"
        }
        create_response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=self.headers)
        client_id = create_response.json()["id"]
        
        # Update status
        update_response = requests.put(f"{BASE_URL}/api/clients/{client_id}", 
            json={"status": "contacted"}, headers=self.headers)
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "contacted"
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/clients/{client_id}", headers=self.headers)
        assert get_response.json()["status"] == "contacted"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=self.headers)
    
    def test_filter_clients_by_status(self):
        """Test filtering clients by status"""
        response = requests.get(f"{BASE_URL}/api/clients", 
            params={"status": "new"}, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # All returned clients should have status 'new'
        for client in data:
            assert client["status"] == "new"


class TestNotesEndpoints:
    """Notes CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create test client"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a client for notes
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        clients = clients_response.json()
        self.client_id = clients[0]["id"] if clients else None
    
    def test_create_note(self):
        """Test creating a note for a client"""
        if not self.client_id:
            pytest.skip("No client available for note test")
        
        note_data = {
            "client_id": self.client_id,
            "text": "TEST_Supabase migration note"
        }
        response = requests.post(f"{BASE_URL}/api/notes", json=note_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == note_data["text"]
        assert data["client_id"] == self.client_id
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/notes/{data['id']}", headers=self.headers)
    
    def test_get_notes_for_client(self):
        """Test getting notes for a client"""
        if not self.client_id:
            pytest.skip("No client available for note test")
        
        response = requests.get(f"{BASE_URL}/api/notes/{self.client_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestRemindersEndpoints:
    """Reminders CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create test client"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a client for reminders
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        clients = clients_response.json()
        self.client_id = clients[0]["id"] if clients else None
    
    def test_get_reminders(self):
        """Test getting reminders list"""
        response = requests.get(f"{BASE_URL}/api/reminders", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_overdue_reminders(self):
        """Test getting overdue reminders"""
        response = requests.get(f"{BASE_URL}/api/reminders/overdue", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_reminder(self):
        """Test creating a reminder"""
        if not self.client_id:
            pytest.skip("No client available for reminder test")
        
        future_time = (datetime.now() + timedelta(days=1)).isoformat()
        reminder_data = {
            "client_id": self.client_id,
            "text": "TEST_Supabase reminder",
            "remind_at": future_time
        }
        response = requests.post(f"{BASE_URL}/api/reminders", json=reminder_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == reminder_data["text"]
        assert data["client_id"] == self.client_id
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/reminders/{data['id']}", headers=self.headers)
    
    def test_complete_reminder(self):
        """Test completing a reminder"""
        if not self.client_id:
            pytest.skip("No client available for reminder test")
        
        # Create reminder
        future_time = (datetime.now() + timedelta(days=1)).isoformat()
        reminder_data = {
            "client_id": self.client_id,
            "text": "TEST_Complete reminder",
            "remind_at": future_time
        }
        create_response = requests.post(f"{BASE_URL}/api/reminders", json=reminder_data, headers=self.headers)
        reminder_id = create_response.json()["id"]
        
        # Complete it
        update_response = requests.put(f"{BASE_URL}/api/reminders/{reminder_id}",
            json={"is_completed": True}, headers=self.headers)
        assert update_response.status_code == 200
        assert update_response.json()["is_completed"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/reminders/{reminder_id}", headers=self.headers)


class TestPaymentsEndpoints:
    """Payments CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create test client"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a client for payments
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        clients = clients_response.json()
        self.client_id = clients[0]["id"] if clients else None
    
    def test_get_payments(self):
        """Test getting all payments"""
        response = requests.get(f"{BASE_URL}/api/payments", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_payment(self):
        """Test creating a payment"""
        if not self.client_id:
            pytest.skip("No client available for payment test")
        
        payment_data = {
            "client_id": self.client_id,
            "amount": 100.00,
            "currency": "USD",
            "status": "pending",
            "comment": "TEST_Supabase payment"
        }
        response = requests.post(f"{BASE_URL}/api/payments", json=payment_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == payment_data["amount"]
        assert data["client_id"] == self.client_id
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payments/{data['id']}", headers=self.headers)
    
    def test_get_client_payments(self):
        """Test getting payments for a specific client"""
        if not self.client_id:
            pytest.skip("No client available for payment test")
        
        response = requests.get(f"{BASE_URL}/api/payments/client/{self.client_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_payment_status(self):
        """Test updating payment status"""
        if not self.client_id:
            pytest.skip("No client available for payment test")
        
        # Create payment
        payment_data = {
            "client_id": self.client_id,
            "amount": 50.00,
            "status": "pending"
        }
        create_response = requests.post(f"{BASE_URL}/api/payments", json=payment_data, headers=self.headers)
        payment_id = create_response.json()["id"]
        
        # Update status
        update_response = requests.put(f"{BASE_URL}/api/payments/{payment_id}",
            json={"status": "paid"}, headers=self.headers)
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "paid"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payments/{payment_id}", headers=self.headers)


class TestTariffsEndpoints:
    """Tariffs CRUD endpoint tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_tariffs(self):
        """Test getting tariffs list"""
        response = requests.get(f"{BASE_URL}/api/tariffs", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify migrated tariffs exist
        assert len(data) >= 3, "Expected at least 3 migrated tariffs"
    
    def test_create_tariff(self):
        """Test creating a tariff"""
        tariff_data = {
            "name": "TEST_Supabase Tariff",
            "price": 199.99,
            "currency": "USD",
            "description": "Test tariff for Supabase migration"
        }
        response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == tariff_data["name"]
        assert data["price"] == tariff_data["price"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tariffs/{data['id']}", headers=self.headers)


class TestGroupsEndpoints:
    """Groups CRUD endpoint tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_groups(self):
        """Test getting groups list"""
        response = requests.get(f"{BASE_URL}/api/groups", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify migrated groups exist
        assert len(data) >= 3, "Expected at least 3 migrated groups"
    
    def test_create_group(self):
        """Test creating a group"""
        group_data = {
            "name": "TEST_Supabase Group",
            "color": "#FF5733",
            "description": "Test group for Supabase migration"
        }
        response = requests.post(f"{BASE_URL}/api/groups", json=group_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == group_data["name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/groups/{data['id']}", headers=self.headers)


class TestStatusesEndpoints:
    """Statuses endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_statuses(self):
        """Test getting statuses list"""
        response = requests.get(f"{BASE_URL}/api/statuses", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify migrated statuses exist
        assert len(data) >= 5, "Expected at least 5 migrated statuses"
        # Check for expected statuses
        status_names = [s["name"] for s in data]
        assert "new" in status_names
        assert "contacted" in status_names
        assert "sold" in status_names


class TestSettingsEndpoints:
    """Settings endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_settings(self):
        """Test getting settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have currency setting
        assert "currency" in data


class TestUsersEndpoints:
    """Users endpoint tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_users(self):
        """Test getting users list"""
        response = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify migrated users exist
        assert len(data) >= 3, "Expected at least 3 migrated users"
        # Check admin user exists
        admin_users = [u for u in data if u["email"] == ADMIN_EMAIL]
        assert len(admin_users) == 1


class TestActivityLogEndpoints:
    """Activity log endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_activity_log(self):
        """Test getting activity log"""
        response = requests.get(f"{BASE_URL}/api/activity-log", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDatabaseStatus:
    """Database status endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_database_status(self):
        """Test database status endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/database-status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "Supabase PostgreSQL"
        # Verify collections have data
        assert "collections" in data
        assert data["collections"]["users"] >= 3
        assert data["collections"]["clients"] >= 9
        assert data["collections"]["tariffs"] >= 3
        assert data["collections"]["groups"] >= 3
        assert data["collections"]["statuses"] >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
