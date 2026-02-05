"""
Phase 3 Features 2 & 3: Tariff Management and Currency Settings API Tests
Tests for:
- /api/tariffs CRUD endpoints
- /api/settings endpoint for currency
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@crm.local"
ADMIN_PASSWORD = "admin123"

# Test data prefix for cleanup
TEST_PREFIX = "TEST_TARIFF_"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def manager_token(admin_headers):
    """Create a manager user and get their token"""
    # Create manager user
    manager_email = f"test_manager_{uuid.uuid4().hex[:8]}@test.local"
    create_response = requests.post(f"{BASE_URL}/api/users", json={
        "name": "Test Manager",
        "email": manager_email,
        "phone": "+998901234567",
        "password": "manager123",
        "role": "manager"
    }, headers=admin_headers)
    
    if create_response.status_code != 200:
        pytest.skip("Could not create manager user for testing")
    
    manager_id = create_response.json()["id"]
    
    # Login as manager
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": manager_email,
        "password": "manager123"
    })
    
    if login_response.status_code != 200:
        pytest.skip("Could not login as manager")
    
    token = login_response.json()["token"]
    
    yield token
    
    # Cleanup: delete manager user
    requests.delete(f"{BASE_URL}/api/users/{manager_id}", headers=admin_headers)


@pytest.fixture(scope="module")
def manager_headers(manager_token):
    """Headers with manager auth token"""
    return {
        "Authorization": f"Bearer {manager_token}",
        "Content-Type": "application/json"
    }


class TestTariffEndpoints:
    """Test /api/tariffs CRUD endpoints"""
    
    created_tariff_ids = []
    
    def test_get_tariffs_as_admin(self, admin_headers):
        """Admin can get list of tariffs"""
        response = requests.get(f"{BASE_URL}/api/tariffs", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ GET /api/tariffs returns {len(response.json())} tariffs")
    
    def test_create_tariff_as_admin(self, admin_headers):
        """Admin can create a new tariff"""
        tariff_data = {
            "name": f"{TEST_PREFIX}Basic_Plan",
            "price": 100.00,
            "currency": "USD",
            "description": "Basic course plan"
        }
        response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=admin_headers)
        assert response.status_code == 200, f"Create tariff failed: {response.text}"
        
        data = response.json()
        assert data["name"] == tariff_data["name"]
        assert data["price"] == tariff_data["price"]
        assert data["currency"] == tariff_data["currency"]
        assert data["description"] == tariff_data["description"]
        assert "id" in data
        
        self.created_tariff_ids.append(data["id"])
        print(f"✓ POST /api/tariffs created tariff with id: {data['id']}")
    
    def test_create_tariff_with_uzs_currency(self, admin_headers):
        """Admin can create tariff with UZS currency"""
        tariff_data = {
            "name": f"{TEST_PREFIX}Premium_UZS",
            "price": 1500000,
            "currency": "UZS",
            "description": "Premium plan in UZS"
        }
        response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["currency"] == "UZS"
        assert data["price"] == 1500000
        
        self.created_tariff_ids.append(data["id"])
        print(f"✓ Created tariff with UZS currency: {data['id']}")
    
    def test_create_tariff_without_description(self, admin_headers):
        """Admin can create tariff without description (optional field)"""
        tariff_data = {
            "name": f"{TEST_PREFIX}NoDesc_Plan",
            "price": 50.00,
            "currency": "USD"
        }
        response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == tariff_data["name"]
        assert data.get("description", "") == ""
        
        self.created_tariff_ids.append(data["id"])
        print(f"✓ Created tariff without description: {data['id']}")
    
    def test_create_tariff_as_manager_fails(self, manager_headers):
        """Manager cannot create tariffs (admin only)"""
        tariff_data = {
            "name": f"{TEST_PREFIX}Manager_Attempt",
            "price": 100.00,
            "currency": "USD"
        }
        response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=manager_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Manager correctly denied from creating tariffs")
    
    def test_update_tariff_as_admin(self, admin_headers):
        """Admin can update an existing tariff"""
        # First create a tariff to update
        create_data = {
            "name": f"{TEST_PREFIX}ToUpdate",
            "price": 75.00,
            "currency": "USD",
            "description": "Original description"
        }
        create_response = requests.post(f"{BASE_URL}/api/tariffs", json=create_data, headers=admin_headers)
        assert create_response.status_code == 200
        tariff_id = create_response.json()["id"]
        self.created_tariff_ids.append(tariff_id)
        
        # Update the tariff
        update_data = {
            "name": f"{TEST_PREFIX}Updated_Plan",
            "price": 150.00,
            "description": "Updated description"
        }
        update_response = requests.put(f"{BASE_URL}/api/tariffs/{tariff_id}", json=update_data, headers=admin_headers)
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
        assert data["description"] == update_data["description"]
        print(f"✓ PUT /api/tariffs/{tariff_id} updated successfully")
    
    def test_update_tariff_as_manager_fails(self, manager_headers, admin_headers):
        """Manager cannot update tariffs"""
        # Create a tariff first
        create_data = {
            "name": f"{TEST_PREFIX}ManagerUpdateTest",
            "price": 100.00,
            "currency": "USD"
        }
        create_response = requests.post(f"{BASE_URL}/api/tariffs", json=create_data, headers=admin_headers)
        tariff_id = create_response.json()["id"]
        self.created_tariff_ids.append(tariff_id)
        
        # Try to update as manager
        update_response = requests.put(f"{BASE_URL}/api/tariffs/{tariff_id}", json={"price": 200.00}, headers=manager_headers)
        assert update_response.status_code == 403
        print("✓ Manager correctly denied from updating tariffs")
    
    def test_delete_tariff_as_admin(self, admin_headers):
        """Admin can delete a tariff not in use"""
        # Create a tariff to delete
        create_data = {
            "name": f"{TEST_PREFIX}ToDelete",
            "price": 25.00,
            "currency": "USD"
        }
        create_response = requests.post(f"{BASE_URL}/api/tariffs", json=create_data, headers=admin_headers)
        assert create_response.status_code == 200
        tariff_id = create_response.json()["id"]
        
        # Delete the tariff
        delete_response = requests.delete(f"{BASE_URL}/api/tariffs/{tariff_id}", headers=admin_headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Tariff deleted"
        print(f"✓ DELETE /api/tariffs/{tariff_id} successful")
    
    def test_delete_tariff_in_use_fails(self, admin_headers):
        """Cannot delete tariff that is assigned to a client"""
        # Create a tariff
        tariff_data = {
            "name": f"{TEST_PREFIX}InUse",
            "price": 200.00,
            "currency": "USD"
        }
        tariff_response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=admin_headers)
        assert tariff_response.status_code == 200
        tariff_id = tariff_response.json()["id"]
        self.created_tariff_ids.append(tariff_id)
        
        # Create a client using this tariff
        client_data = {
            "name": f"{TEST_PREFIX}Client",
            "phone": f"+998{uuid.uuid4().hex[:9]}",
            "tariff_id": tariff_id
        }
        client_response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        assert client_response.status_code == 200
        client_id = client_response.json()["id"]
        
        # Try to delete the tariff - should fail
        delete_response = requests.delete(f"{BASE_URL}/api/tariffs/{tariff_id}", headers=admin_headers)
        assert delete_response.status_code == 400
        assert "in use" in delete_response.json()["detail"].lower()
        print("✓ Delete tariff in use correctly returns 400 error")
        
        # Cleanup: delete the client
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
    
    def test_delete_tariff_as_manager_fails(self, manager_headers, admin_headers):
        """Manager cannot delete tariffs"""
        # Create a tariff
        create_data = {
            "name": f"{TEST_PREFIX}ManagerDeleteTest",
            "price": 100.00,
            "currency": "USD"
        }
        create_response = requests.post(f"{BASE_URL}/api/tariffs", json=create_data, headers=admin_headers)
        tariff_id = create_response.json()["id"]
        self.created_tariff_ids.append(tariff_id)
        
        # Try to delete as manager
        delete_response = requests.delete(f"{BASE_URL}/api/tariffs/{tariff_id}", headers=manager_headers)
        assert delete_response.status_code == 403
        print("✓ Manager correctly denied from deleting tariffs")
    
    def test_get_tariffs_as_manager(self, manager_headers):
        """Manager can view tariffs (for client assignment)"""
        response = requests.get(f"{BASE_URL}/api/tariffs", headers=manager_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✓ Manager can view tariffs list")
    
    @pytest.fixture(autouse=True, scope="class")
    def cleanup_tariffs(self, admin_headers):
        """Cleanup test tariffs after all tests in class"""
        yield
        for tariff_id in self.created_tariff_ids:
            try:
                requests.delete(f"{BASE_URL}/api/tariffs/{tariff_id}", headers=admin_headers)
            except:
                pass
        self.created_tariff_ids.clear()


class TestSettingsEndpoints:
    """Test /api/settings endpoint for currency"""
    
    original_currency = None
    
    def test_get_settings_as_admin(self, admin_headers):
        """Admin can get system settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "currency" in data
        self.original_currency = data["currency"]
        print(f"✓ GET /api/settings returns currency: {data['currency']}")
    
    def test_update_currency_to_uzs(self, admin_headers):
        """Admin can switch currency to UZS"""
        response = requests.put(f"{BASE_URL}/api/settings", json={"currency": "UZS"}, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["currency"] == "UZS"
        print("✓ PUT /api/settings updated currency to UZS")
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=admin_headers)
        assert get_response.json()["currency"] == "UZS"
        print("✓ Currency change persisted to database")
    
    def test_update_currency_to_usd(self, admin_headers):
        """Admin can switch currency to USD"""
        response = requests.put(f"{BASE_URL}/api/settings", json={"currency": "USD"}, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["currency"] == "USD"
        print("✓ PUT /api/settings updated currency to USD")
    
    def test_update_settings_as_manager_fails(self, manager_headers):
        """Manager cannot update system settings"""
        response = requests.put(f"{BASE_URL}/api/settings", json={"currency": "UZS"}, headers=manager_headers)
        assert response.status_code == 403
        print("✓ Manager correctly denied from updating settings")
    
    def test_get_settings_as_manager(self, manager_headers):
        """Manager can view settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=manager_headers)
        assert response.status_code == 200
        assert "currency" in response.json()
        print("✓ Manager can view settings")
    
    def test_dashboard_stats_includes_currency(self, admin_headers):
        """Dashboard stats endpoint returns system currency"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "currency" in data
        print(f"✓ Dashboard stats includes currency: {data['currency']}")


class TestTariffIntegration:
    """Test tariff integration with clients"""
    
    def test_client_with_tariff_shows_tariff_info(self, admin_headers):
        """Client with tariff_id returns tariff name and price"""
        # Create a tariff
        tariff_data = {
            "name": f"{TEST_PREFIX}Integration_Test",
            "price": 500.00,
            "currency": "USD"
        }
        tariff_response = requests.post(f"{BASE_URL}/api/tariffs", json=tariff_data, headers=admin_headers)
        assert tariff_response.status_code == 200
        tariff_id = tariff_response.json()["id"]
        
        # Create a client with this tariff
        client_data = {
            "name": f"{TEST_PREFIX}Integration_Client",
            "phone": f"+998{uuid.uuid4().hex[:9]}",
            "tariff_id": tariff_id
        }
        client_response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        assert client_response.status_code == 200
        client_id = client_response.json()["id"]
        
        # Get client and verify tariff info
        get_response = requests.get(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        assert get_response.status_code == 200
        
        client = get_response.json()
        assert client["tariff_id"] == tariff_id
        assert client.get("tariff_name") == tariff_data["name"]
        assert client.get("tariff_price") == tariff_data["price"]
        print("✓ Client with tariff returns tariff_name and tariff_price")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/tariffs/{tariff_id}", headers=admin_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
