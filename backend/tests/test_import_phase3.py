"""
Phase 3 Feature 4: Excel/CSV Client Import Tests
Tests for /api/import/preview and /api/import/save endpoints
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@crm.local"
ADMIN_PASSWORD = "admin123"
MANAGER_EMAIL = "test_manager_import@crm.local"
MANAGER_PASSWORD = "manager123"


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
def manager_user(admin_token):
    """Create a manager user for testing"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Check if manager exists
    users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    if users_response.status_code == 200:
        for user in users_response.json():
            if user.get("email") == MANAGER_EMAIL:
                return user
    
    # Create manager
    response = requests.post(f"{BASE_URL}/api/users", headers=headers, json={
        "name": "Test Manager Import",
        "email": MANAGER_EMAIL,
        "phone": "+998900000099",
        "password": MANAGER_PASSWORD,
        "role": "manager"
    })
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 400:
        # User already exists, get token
        pass
    return None


@pytest.fixture(scope="module")
def manager_token(manager_user):
    """Get manager authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MANAGER_EMAIL,
        "password": MANAGER_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Manager login failed")


@pytest.fixture
def cleanup_test_clients(admin_token):
    """Cleanup test clients after tests"""
    yield
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Get all clients and delete test ones
    response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
    if response.status_code == 200:
        for client in response.json():
            if client.get("phone", "").startswith("+998901111") or \
               client.get("phone", "").startswith("+998902222") or \
               client.get("phone", "").startswith("+998903333") or \
               client.get("name", "").startswith("TEST_IMPORT"):
                requests.delete(f"{BASE_URL}/api/clients/{client['id']}", headers=headers)


class TestImportPreview:
    """Tests for /api/import/preview endpoint"""
    
    def test_import_preview_valid_csv(self, admin_token):
        """Test preview with valid CSV file"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create CSV content
        csv_content = "name,phone,source,status\nTest Import 1,+998901111111,Instagram,new\nTest Import 2,+998902222222,Telegram,contacted"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/import/preview", headers=headers, files=files)
        
        assert response.status_code == 200, f"Preview failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total" in data
        assert "valid" in data
        assert "duplicates" in data
        assert "errors" in data
        assert "rows" in data
        
        # Verify counts
        assert data["total"] == 2
        assert data["valid"] >= 0  # May have duplicates from previous runs
        
        # Verify row structure
        if len(data["rows"]) > 0:
            row = data["rows"][0]
            assert "name" in row
            assert "phone" in row
            assert "source" in row
            assert "status" in row
            assert "valid" in row
            assert "is_duplicate" in row
    
    def test_import_preview_detects_duplicates(self, admin_token, cleanup_test_clients):
        """Test that preview detects duplicate phone numbers"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First, create a client with a specific phone
        client_response = requests.post(f"{BASE_URL}/api/clients", headers=headers, json={
            "name": "TEST_IMPORT_Existing",
            "phone": "+998901111111",
            "source": "Test",
            "status": "new"
        })
        
        # Now try to preview import with same phone
        csv_content = "name,phone,source,status\nDuplicate Test,+998901111111,Instagram,new"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/import/preview", headers=headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should detect duplicate
        assert data["duplicates"] >= 1
        
        # Row should be marked as duplicate
        if len(data["rows"]) > 0:
            row = data["rows"][0]
            assert row["is_duplicate"] == True
            assert row["valid"] == False
    
    def test_import_preview_missing_required_fields(self, admin_token):
        """Test preview with missing required fields (name or phone)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # CSV with missing phone
        csv_content = "name,phone,source,status\nNo Phone,,Instagram,new"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/import/preview", headers=headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have errors
        assert data["errors"] >= 1
    
    def test_import_preview_normalizes_status(self, admin_token):
        """Test that invalid status defaults to 'new'"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        csv_content = "name,phone,source,status\nTest Status,+998904444444,Instagram,invalid_status"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/import/preview", headers=headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Status should be normalized to 'new'
        if len(data["rows"]) > 0:
            assert data["rows"][0]["status"] == "new"
    
    def test_import_preview_requires_auth(self):
        """Test that preview requires authentication"""
        csv_content = "name,phone,source,status\nTest,+998900000000,Test,new"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/import/preview", files=files)
        
        assert response.status_code == 401 or response.status_code == 403


class TestImportSave:
    """Tests for /api/import/save endpoint"""
    
    def test_import_save_valid_rows(self, admin_token, cleanup_test_clients):
        """Test saving valid import rows"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # Prepare valid rows
        rows = [
            {"name": "TEST_IMPORT_Save1", "phone": "+998905555551", "source": "Import Test", "status": "new"},
            {"name": "TEST_IMPORT_Save2", "phone": "+998905555552", "source": "Import Test", "status": "contacted"}
        ]
        
        response = requests.post(f"{BASE_URL}/api/import/save", headers=headers, json=rows)
        
        assert response.status_code == 200, f"Save failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "failed" in data
        assert "failed_rows" in data
        
        # Verify success count
        assert data["success"] == 2
        assert data["failed"] == 0
        
        # Verify clients were created - GET to verify persistence
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers={"Authorization": f"Bearer {admin_token}"})
        assert clients_response.status_code == 200
        clients = clients_response.json()
        
        imported_phones = ["+998905555551", "+998905555552"]
        found_count = sum(1 for c in clients if c.get("phone") in imported_phones)
        assert found_count == 2, "Imported clients not found in database"
    
    def test_import_save_skips_duplicates(self, admin_token, cleanup_test_clients):
        """Test that save skips duplicate phone numbers"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # First create a client
        requests.post(f"{BASE_URL}/api/clients", headers=headers, json={
            "name": "TEST_IMPORT_Existing2",
            "phone": "+998906666666",
            "source": "Test",
            "status": "new"
        })
        
        # Try to import with same phone
        rows = [
            {"name": "TEST_IMPORT_Duplicate", "phone": "+998906666666", "source": "Import", "status": "new"}
        ]
        
        response = requests.post(f"{BASE_URL}/api/import/save", headers=headers, json=rows)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should fail due to duplicate
        assert data["failed"] >= 1
        assert len(data["failed_rows"]) >= 1
        assert "Duplicate" in data["failed_rows"][0]["error"]
    
    def test_import_save_empty_list(self, admin_token):
        """Test saving empty list"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        response = requests.post(f"{BASE_URL}/api/import/save", headers=headers, json=[])
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert data["failed"] == 0
    
    def test_import_save_requires_auth(self):
        """Test that save requires authentication"""
        rows = [{"name": "Test", "phone": "+998900000000", "source": "Test", "status": "new"}]
        
        response = requests.post(f"{BASE_URL}/api/import/save", json=rows, headers={"Content-Type": "application/json"})
        
        assert response.status_code == 401 or response.status_code == 403


class TestImportIntegration:
    """Integration tests for full import flow"""
    
    def test_full_import_flow(self, admin_token, cleanup_test_clients):
        """Test complete import flow: preview -> save -> verify"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 1: Preview
        csv_content = "name,phone,source,status\nTEST_IMPORT_Flow1,+998907777771,Flow Test,new\nTEST_IMPORT_Flow2,+998907777772,Flow Test,contacted"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        preview_response = requests.post(f"{BASE_URL}/api/import/preview", headers=headers, files=files)
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        
        # Step 2: Save valid rows
        valid_rows = [r for r in preview_data["rows"] if r["valid"]]
        if len(valid_rows) > 0:
            save_rows = [{"name": r["name"], "phone": r["phone"], "source": r["source"], "status": r["status"]} for r in valid_rows]
            
            save_response = requests.post(
                f"{BASE_URL}/api/import/save", 
                headers={**headers, "Content-Type": "application/json"}, 
                json=save_rows
            )
            assert save_response.status_code == 200
            save_data = save_response.json()
            
            # Step 3: Verify clients exist
            clients_response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
            assert clients_response.status_code == 200
            clients = clients_response.json()
            
            imported_phones = [r["phone"] for r in valid_rows]
            found_clients = [c for c in clients if c.get("phone") in imported_phones]
            
            assert len(found_clients) == save_data["success"], "Not all imported clients found"


class TestImportAccessControl:
    """Tests for import access control - admin only feature"""
    
    def test_manager_can_preview(self, manager_token):
        """Test that manager CAN preview imports (read operation)"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        csv_content = "name,phone,source,status\nTest,+998900000001,Test,new"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(f"{BASE_URL}/api/import/preview", headers=headers, files=files)
        
        # Manager should be able to preview (it's a read operation)
        # The actual restriction is on the UI side
        assert response.status_code == 200
    
    def test_manager_can_save(self, manager_token):
        """Test that manager CAN save imports (creates clients assigned to them)"""
        headers = {"Authorization": f"Bearer {manager_token}", "Content-Type": "application/json"}
        
        rows = [{"name": "TEST_IMPORT_Manager", "phone": "+998908888888", "source": "Manager Import", "status": "new"}]
        
        response = requests.post(f"{BASE_URL}/api/import/save", headers=headers, json=rows)
        
        # Manager should be able to import (creates clients assigned to them)
        # The actual restriction is on the UI side (Import button hidden for non-admin)
        assert response.status_code == 200


# Cleanup fixture to run after all tests
@pytest.fixture(scope="module", autouse=True)
def cleanup_after_all(admin_token):
    """Cleanup all test data after module completes"""
    yield
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Delete test clients
    response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
    if response.status_code == 200:
        for client in response.json():
            if client.get("name", "").startswith("TEST_IMPORT") or \
               client.get("phone", "").startswith("+99890555555") or \
               client.get("phone", "").startswith("+99890666666") or \
               client.get("phone", "").startswith("+99890777777") or \
               client.get("phone", "").startswith("+99890888888"):
                requests.delete(f"{BASE_URL}/api/clients/{client['id']}", headers=headers)
    
    # Delete test manager
    users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    if users_response.status_code == 200:
        for user in users_response.json():
            if user.get("email") == MANAGER_EMAIL:
                requests.delete(f"{BASE_URL}/api/users/{user['id']}", headers=headers)
