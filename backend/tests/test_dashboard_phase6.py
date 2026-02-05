"""
Dashboard API Tests - Phase 6
Tests for dashboard stats, analytics, manager stats, recent clients/notes
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@crm.local"
ADMIN_PASSWORD = "admin123"


class TestDashboardEndpoints:
    """Dashboard endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # ==================== /api/dashboard/stats ====================
    
    def test_dashboard_stats_returns_200(self):
        """Test /api/dashboard/stats returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ /api/dashboard/stats returns 200")
    
    def test_dashboard_stats_structure(self):
        """Test /api/dashboard/stats returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "total_clients", "todays_leads", "new_count", "contacted_count",
            "sold_count", "total_paid", "total_pending", "overdue_reminders", "currency"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(data["total_clients"], int), "total_clients should be int"
        assert isinstance(data["todays_leads"], int), "todays_leads should be int"
        assert isinstance(data["new_count"], int), "new_count should be int"
        assert isinstance(data["contacted_count"], int), "contacted_count should be int"
        assert isinstance(data["sold_count"], int), "sold_count should be int"
        assert isinstance(data["total_paid"], (int, float)), "total_paid should be numeric"
        assert isinstance(data["total_pending"], (int, float)), "total_pending should be numeric"
        assert isinstance(data["currency"], str), "currency should be string"
        
        print(f"✓ Dashboard stats structure valid: {data}")
    
    def test_dashboard_stats_requires_auth(self):
        """Test /api/dashboard/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ /api/dashboard/stats requires authentication")
    
    # ==================== /api/dashboard/recent-clients ====================
    
    def test_recent_clients_returns_200(self):
        """Test /api/dashboard/recent-clients returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-clients", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ /api/dashboard/recent-clients returns 200")
    
    def test_recent_clients_returns_list(self):
        """Test /api/dashboard/recent-clients returns a list"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-clients", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "recent-clients should return a list"
        print(f"✓ Recent clients returns list with {len(data)} items")
    
    def test_recent_clients_structure(self):
        """Test recent clients have correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-clients", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            client = data[0]
            assert "id" in client, "Client should have id"
            assert "name" in client, "Client should have name"
            assert "phone" in client, "Client should have phone"
            assert "status" in client, "Client should have status"
            print(f"✓ Recent client structure valid: {list(client.keys())}")
        else:
            print("✓ Recent clients list is empty (no clients in system)")
    
    # ==================== /api/dashboard/recent-notes ====================
    
    def test_recent_notes_returns_200(self):
        """Test /api/dashboard/recent-notes returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-notes", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ /api/dashboard/recent-notes returns 200")
    
    def test_recent_notes_returns_list(self):
        """Test /api/dashboard/recent-notes returns a list"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-notes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "recent-notes should return a list"
        print(f"✓ Recent notes returns list with {len(data)} items")
    
    # ==================== /api/dashboard/manager-stats ====================
    
    def test_manager_stats_returns_200(self):
        """Test /api/dashboard/manager-stats returns 200 for admin"""
        response = requests.get(f"{BASE_URL}/api/dashboard/manager-stats", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ /api/dashboard/manager-stats returns 200")
    
    def test_manager_stats_returns_list(self):
        """Test /api/dashboard/manager-stats returns a list"""
        response = requests.get(f"{BASE_URL}/api/dashboard/manager-stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "manager-stats should return a list"
        print(f"✓ Manager stats returns list with {len(data)} managers")
    
    def test_manager_stats_structure(self):
        """Test manager stats have correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/manager-stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            manager = data[0]
            required_fields = ["id", "name", "role", "sold_count", "total_revenue", "total_clients"]
            for field in required_fields:
                assert field in manager, f"Manager should have {field}"
            print(f"✓ Manager stats structure valid: {list(manager.keys())}")
        else:
            print("✓ Manager stats list is empty (no managers)")
    
    # ==================== /api/dashboard/analytics ====================
    
    def test_analytics_returns_200(self):
        """Test /api/dashboard/analytics returns 200 for admin"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ /api/dashboard/analytics returns 200")
    
    def test_analytics_structure(self):
        """Test /api/dashboard/analytics returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["monthly_data", "tariff_stats", "summary", "currency"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check monthly_data is a list
        assert isinstance(data["monthly_data"], list), "monthly_data should be a list"
        
        # Check tariff_stats is a list
        assert isinstance(data["tariff_stats"], list), "tariff_stats should be a list"
        
        # Check summary structure
        summary = data["summary"]
        summary_fields = ["total_revenue", "total_deals", "total_leads", 
                         "revenue_change", "revenue_change_pct", "deals_change", "deals_change_pct"]
        for field in summary_fields:
            assert field in summary, f"Summary missing field: {field}"
        
        print(f"✓ Analytics structure valid: {list(data.keys())}")
        print(f"  - Monthly data: {len(data['monthly_data'])} months")
        print(f"  - Tariff stats: {len(data['tariff_stats'])} tariffs")
        print(f"  - Summary: {summary}")
    
    def test_analytics_monthly_data_structure(self):
        """Test monthly data has correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["monthly_data"]) > 0:
            month = data["monthly_data"][0]
            required_fields = ["month", "month_name", "sold_count", "revenue", "new_leads"]
            for field in required_fields:
                assert field in month, f"Monthly data missing field: {field}"
            print(f"✓ Monthly data structure valid: {list(month.keys())}")
        else:
            print("✓ Monthly data is empty")
    
    def test_analytics_tariff_stats_structure(self):
        """Test tariff stats have correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["tariff_stats"]) > 0:
            tariff = data["tariff_stats"][0]
            required_fields = ["name", "price", "sold_count", "revenue"]
            for field in required_fields:
                assert field in tariff, f"Tariff stats missing field: {field}"
            print(f"✓ Tariff stats structure valid: {list(tariff.keys())}")
        else:
            print("✓ Tariff stats is empty (no tariffs)")
    
    def test_analytics_with_months_param(self):
        """Test /api/dashboard/analytics accepts months parameter"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics?months=3", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should return approximately 3-4 months of data
        assert len(data["monthly_data"]) <= 5, "Should return limited months of data"
        print(f"✓ Analytics with months=3 returns {len(data['monthly_data'])} months")
    
    # ==================== /api/reminders/overdue ====================
    
    def test_overdue_reminders_returns_200(self):
        """Test /api/reminders/overdue returns 200"""
        response = requests.get(f"{BASE_URL}/api/reminders/overdue", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ /api/reminders/overdue returns 200")
    
    def test_overdue_reminders_returns_list(self):
        """Test /api/reminders/overdue returns a list"""
        response = requests.get(f"{BASE_URL}/api/reminders/overdue", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "overdue reminders should return a list"
        print(f"✓ Overdue reminders returns list with {len(data)} items")


class TestDashboardNonAdminAccess:
    """Test dashboard access for non-admin users"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - create manager user and get token"""
        # First login as admin
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert admin_response.status_code == 200
        admin_token = admin_response.json()["token"]
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # Create a test manager user
        self.manager_email = "TEST_manager_dashboard@test.com"
        self.manager_password = "testpass123"
        
        # Check if manager exists, if not create
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_response.json()
        manager_exists = any(u["email"] == self.manager_email for u in users)
        
        if not manager_exists:
            create_response = requests.post(f"{BASE_URL}/api/users", headers=admin_headers, json={
                "name": "Test Manager Dashboard",
                "email": self.manager_email,
                "phone": "+998901234567",
                "password": self.manager_password,
                "role": "manager"
            })
            if create_response.status_code != 200:
                pytest.skip(f"Could not create test manager: {create_response.text}")
        
        # Login as manager
        manager_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.manager_email,
            "password": self.manager_password
        })
        if manager_login.status_code != 200:
            pytest.skip(f"Could not login as manager: {manager_login.text}")
        
        self.manager_token = manager_login.json()["token"]
        self.manager_headers = {
            "Authorization": f"Bearer {self.manager_token}",
            "Content-Type": "application/json"
        }
        self.admin_headers = admin_headers
    
    def test_manager_can_access_dashboard_stats(self):
        """Test manager can access /api/dashboard/stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.manager_headers)
        assert response.status_code == 200, f"Manager should access stats: {response.text}"
        print("✓ Manager can access /api/dashboard/stats")
    
    def test_manager_cannot_access_manager_stats(self):
        """Test manager cannot access /api/dashboard/manager-stats (admin only)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/manager-stats", headers=self.manager_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Manager cannot access /api/dashboard/manager-stats (admin only)")
    
    def test_manager_cannot_access_analytics(self):
        """Test manager cannot access /api/dashboard/analytics (admin only)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/analytics", headers=self.manager_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Manager cannot access /api/dashboard/analytics (admin only)")
    
    def test_manager_can_access_recent_clients(self):
        """Test manager can access /api/dashboard/recent-clients"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-clients", headers=self.manager_headers)
        assert response.status_code == 200, f"Manager should access recent clients: {response.text}"
        print("✓ Manager can access /api/dashboard/recent-clients")
    
    def test_manager_can_access_recent_notes(self):
        """Test manager can access /api/dashboard/recent-notes"""
        response = requests.get(f"{BASE_URL}/api/dashboard/recent-notes", headers=self.manager_headers)
        assert response.status_code == 200, f"Manager should access recent notes: {response.text}"
        print("✓ Manager can access /api/dashboard/recent-notes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
