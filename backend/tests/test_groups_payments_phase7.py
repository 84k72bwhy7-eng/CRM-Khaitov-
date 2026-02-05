"""
Test suite for Phase 7: Groups Management and Payment Edit Features
- Groups CRUD endpoints (admin only)
- Payment update with validation and activity logging
- Client group filtering
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@crm.local"
ADMIN_PASSWORD = "admin123"


class TestSetup:
    """Setup fixtures for testing"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Get headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }


class TestGroupsEndpoints(TestSetup):
    """Test Groups CRUD endpoints"""
    
    def test_get_groups_returns_list(self, admin_headers):
        """GET /api/groups returns list of groups"""
        response = requests.get(f"{BASE_URL}/api/groups", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: GET /api/groups returns {len(data)} groups")
    
    def test_create_group_admin_only(self, admin_headers):
        """POST /api/groups creates a new group (admin only)"""
        group_data = {
            "name": f"TEST_Group_{datetime.now().strftime('%H%M%S')}",
            "color": "#3B82F6",
            "description": "Test group for automated testing"
        }
        response = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == group_data["name"]
        assert data["color"] == group_data["color"]
        assert data["description"] == group_data["description"]
        print(f"SUCCESS: Created group with id={data['id']}")
        return data["id"]
    
    def test_create_group_duplicate_name_fails(self, admin_headers):
        """POST /api/groups with duplicate name returns 400"""
        # First create a group
        unique_name = f"TEST_Duplicate_{datetime.now().strftime('%H%M%S')}"
        group_data = {"name": unique_name, "color": "#22C55E"}
        response1 = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert response1.status_code == 200
        
        # Try to create another with same name
        response2 = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json().get("detail", "").lower()
        print("SUCCESS: Duplicate group name returns 400")
    
    def test_update_group_admin_only(self, admin_headers):
        """PUT /api/groups/{id} updates group (admin only)"""
        # Create a group first
        group_data = {
            "name": f"TEST_Update_{datetime.now().strftime('%H%M%S')}",
            "color": "#F59E0B"
        }
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Update the group
        update_data = {
            "name": f"TEST_Updated_{datetime.now().strftime('%H%M%S')}",
            "color": "#EF4444",
            "description": "Updated description"
        }
        update_response = requests.put(f"{BASE_URL}/api/groups/{group_id}", headers=admin_headers, json=update_data)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == update_data["name"]
        assert data["color"] == update_data["color"]
        assert data["description"] == update_data["description"]
        print(f"SUCCESS: Updated group {group_id}")
    
    def test_delete_group_without_clients(self, admin_headers):
        """DELETE /api/groups/{id} deletes group without clients"""
        # Create a group
        group_data = {
            "name": f"TEST_Delete_{datetime.now().strftime('%H%M%S')}",
            "color": "#8B5CF6"
        }
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Delete the group
        delete_response = requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=admin_headers)
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json().get("message", "").lower()
        print(f"SUCCESS: Deleted group {group_id}")
    
    def test_delete_group_with_clients_fails(self, admin_headers):
        """DELETE /api/groups/{id} fails if clients use the group"""
        # Create a group
        group_data = {
            "name": f"TEST_InUse_{datetime.now().strftime('%H%M%S')}",
            "color": "#EC4899"
        }
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Create a client with this group
        client_data = {
            "name": f"TEST_Client_{datetime.now().strftime('%H%M%S')}",
            "phone": f"+998{datetime.now().strftime('%H%M%S%f')[:9]}",
            "group_id": group_id
        }
        client_response = requests.post(f"{BASE_URL}/api/clients", headers=admin_headers, json=client_data)
        assert client_response.status_code == 200
        client_id = client_response.json()["id"]
        
        # Try to delete the group - should fail
        delete_response = requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=admin_headers)
        assert delete_response.status_code == 400
        assert "clients" in delete_response.json().get("detail", "").lower()
        print("SUCCESS: Cannot delete group with clients (400)")
        
        # Cleanup: delete client first, then group
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=admin_headers)


class TestPaymentUpdate(TestSetup):
    """Test Payment Update functionality"""
    
    @pytest.fixture(scope="class")
    def test_client(self, admin_headers):
        """Create a test client for payment tests"""
        client_data = {
            "name": f"TEST_PaymentClient_{datetime.now().strftime('%H%M%S')}",
            "phone": f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        }
        response = requests.post(f"{BASE_URL}/api/clients", headers=admin_headers, json=client_data)
        assert response.status_code == 200
        return response.json()
    
    def test_create_payment_with_comment(self, admin_headers, test_client):
        """POST /api/payments creates payment with comment field"""
        payment_data = {
            "client_id": test_client["id"],
            "amount": 100.50,
            "currency": "USD",
            "status": "pending",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "comment": "Initial payment for testing"
        }
        response = requests.post(f"{BASE_URL}/api/payments", headers=admin_headers, json=payment_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["amount"] == payment_data["amount"]
        assert data["comment"] == payment_data["comment"]
        print(f"SUCCESS: Created payment with comment, id={data['id']}")
        return data
    
    def test_update_payment_all_fields(self, admin_headers, test_client):
        """PUT /api/payments/{id} updates all payment fields"""
        # Create a payment first
        payment_data = {
            "client_id": test_client["id"],
            "amount": 50.00,
            "currency": "USD",
            "status": "pending",
            "comment": "Original comment"
        }
        create_response = requests.post(f"{BASE_URL}/api/payments", headers=admin_headers, json=payment_data)
        assert create_response.status_code == 200
        payment_id = create_response.json()["id"]
        
        # Update the payment
        update_data = {
            "amount": 75.00,
            "currency": "UZS",
            "status": "paid",
            "date": "2026-01-15",
            "comment": "Updated comment"
        }
        update_response = requests.put(f"{BASE_URL}/api/payments/{payment_id}", headers=admin_headers, json=update_data)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["amount"] == update_data["amount"]
        assert data["currency"] == update_data["currency"]
        assert data["status"] == update_data["status"]
        assert data["date"] == update_data["date"]
        assert data["comment"] == update_data["comment"]
        print(f"SUCCESS: Updated payment {payment_id} with all fields")
    
    def test_update_payment_negative_amount_fails(self, admin_headers, test_client):
        """PUT /api/payments/{id} with negative amount returns 400"""
        # Create a payment first
        payment_data = {
            "client_id": test_client["id"],
            "amount": 100.00,
            "currency": "USD",
            "status": "pending"
        }
        create_response = requests.post(f"{BASE_URL}/api/payments", headers=admin_headers, json=payment_data)
        assert create_response.status_code == 200
        payment_id = create_response.json()["id"]
        
        # Try to update with negative amount
        update_data = {"amount": -50.00}
        update_response = requests.put(f"{BASE_URL}/api/payments/{payment_id}", headers=admin_headers, json=update_data)
        assert update_response.status_code == 400
        assert "negative" in update_response.json().get("detail", "").lower()
        print("SUCCESS: Negative amount returns 400")
    
    def test_update_payment_logs_activity(self, admin_headers, test_client):
        """PUT /api/payments/{id} logs old and new values in activity log"""
        # Create a payment
        payment_data = {
            "client_id": test_client["id"],
            "amount": 200.00,
            "currency": "USD",
            "status": "pending"
        }
        create_response = requests.post(f"{BASE_URL}/api/payments", headers=admin_headers, json=payment_data)
        assert create_response.status_code == 200
        payment_id = create_response.json()["id"]
        
        # Update the payment
        update_data = {"amount": 250.00, "status": "paid"}
        update_response = requests.put(f"{BASE_URL}/api/payments/{payment_id}", headers=admin_headers, json=update_data)
        assert update_response.status_code == 200
        
        # Check activity log
        activity_response = requests.get(f"{BASE_URL}/api/activity-log?entity_type=payment", headers=admin_headers)
        assert activity_response.status_code == 200
        activities = activity_response.json()
        
        # Find the update activity for this payment
        update_activity = None
        for activity in activities:
            if activity.get("entity_id") == payment_id and activity.get("action") == "update":
                update_activity = activity
                break
        
        assert update_activity is not None, "Update activity not found in log"
        details = update_activity.get("details", {})
        assert "changes" in details, "Changes not logged in activity"
        changes = details["changes"]
        
        # Verify old and new values are logged
        if "amount" in changes:
            assert "old" in changes["amount"]
            assert "new" in changes["amount"]
            assert changes["amount"]["old"] == 200.00
            assert changes["amount"]["new"] == 250.00
        
        print(f"SUCCESS: Activity log contains old/new values for payment update")


class TestClientGroupFilter(TestSetup):
    """Test client filtering by group"""
    
    def test_get_clients_with_group_filter(self, admin_headers):
        """GET /api/clients supports group_id filter parameter"""
        # Create a group
        group_data = {
            "name": f"TEST_FilterGroup_{datetime.now().strftime('%H%M%S')}",
            "color": "#06B6D4"
        }
        group_response = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert group_response.status_code == 200
        group_id = group_response.json()["id"]
        
        # Create a client with this group
        client_data = {
            "name": f"TEST_FilterClient_{datetime.now().strftime('%H%M%S')}",
            "phone": f"+998{datetime.now().strftime('%H%M%S%f')[:9]}",
            "group_id": group_id
        }
        client_response = requests.post(f"{BASE_URL}/api/clients", headers=admin_headers, json=client_data)
        assert client_response.status_code == 200
        client_id = client_response.json()["id"]
        
        # Filter clients by group
        filter_response = requests.get(f"{BASE_URL}/api/clients?group_id={group_id}", headers=admin_headers)
        assert filter_response.status_code == 200
        filtered_clients = filter_response.json()
        
        # Verify the client is in the filtered results
        client_ids = [c["id"] for c in filtered_clients]
        assert client_id in client_ids, "Client not found in filtered results"
        
        # Verify all returned clients have the correct group
        for client in filtered_clients:
            assert client.get("group_id") == group_id
        
        print(f"SUCCESS: GET /api/clients?group_id={group_id} returns filtered clients")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=admin_headers)
    
    def test_client_includes_group_info(self, admin_headers):
        """GET /api/clients returns group_name and group_color for clients with groups"""
        # Create a group
        group_data = {
            "name": f"TEST_InfoGroup_{datetime.now().strftime('%H%M%S')}",
            "color": "#84CC16"
        }
        group_response = requests.post(f"{BASE_URL}/api/groups", headers=admin_headers, json=group_data)
        assert group_response.status_code == 200
        group_id = group_response.json()["id"]
        group_name = group_response.json()["name"]
        group_color = group_response.json()["color"]
        
        # Create a client with this group
        client_data = {
            "name": f"TEST_InfoClient_{datetime.now().strftime('%H%M%S')}",
            "phone": f"+998{datetime.now().strftime('%H%M%S%f')[:9]}",
            "group_id": group_id
        }
        client_response = requests.post(f"{BASE_URL}/api/clients", headers=admin_headers, json=client_data)
        assert client_response.status_code == 200
        client_id = client_response.json()["id"]
        
        # Get clients and find our client
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=admin_headers)
        assert clients_response.status_code == 200
        clients = clients_response.json()
        
        our_client = None
        for client in clients:
            if client["id"] == client_id:
                our_client = client
                break
        
        assert our_client is not None
        assert our_client.get("group_name") == group_name
        assert our_client.get("group_color") == group_color
        
        print(f"SUCCESS: Client includes group_name and group_color")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=admin_headers)


class TestCleanup(TestSetup):
    """Cleanup test data"""
    
    def test_cleanup_test_data(self, admin_headers):
        """Clean up TEST_ prefixed data"""
        # Get all groups and delete TEST_ ones
        groups_response = requests.get(f"{BASE_URL}/api/groups", headers=admin_headers)
        if groups_response.status_code == 200:
            for group in groups_response.json():
                if group.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/groups/{group['id']}", headers=admin_headers)
        
        # Get all clients and delete TEST_ ones
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=admin_headers)
        if clients_response.status_code == 200:
            for client in clients_response.json():
                if client.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/clients/{client['id']}", headers=admin_headers)
        
        print("SUCCESS: Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
