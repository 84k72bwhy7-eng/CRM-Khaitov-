"""
Phase 3 Feature 1: Client Creation with Comments & Reminders
Tests for:
- Client creation with initial_comment saves to notes collection
- Client creation with reminder_text and reminder_at creates reminder
- Client creation without optional fields still works
- Tariff selection saved with client
- Backend API /api/clients POST accepts new fields
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestClientCreationPhase3:
    """Test client creation with new Phase 3 fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@crm.local",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_client_ids = []
        yield
        # Cleanup created clients
        for client_id in self.created_client_ids:
            try:
                requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=self.headers)
            except:
                pass
    
    def test_create_client_basic_without_optional_fields(self):
        """Test creating client without initial_comment or reminder - should work"""
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        payload = {
            "name": "TEST_Basic Client",
            "phone": phone,
            "source": "Test",
            "status": "new"
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        self.created_client_ids.append(data["id"])
        
        assert data["name"] == "TEST_Basic Client"
        assert data["phone"] == phone
        assert data["status"] == "new"
        print(f"✓ Created basic client without optional fields: {data['id']}")
    
    def test_create_client_with_initial_comment(self):
        """Test creating client with initial_comment - should save to notes collection"""
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        initial_comment = "This is the initial comment for the new client"
        
        payload = {
            "name": "TEST_Client With Comment",
            "phone": phone,
            "source": "Instagram",
            "status": "new",
            "initial_comment": initial_comment
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        # Verify client was created
        assert data["name"] == "TEST_Client With Comment"
        print(f"✓ Created client with initial_comment: {client_id}")
        
        # Verify note was created in notes collection
        notes_response = requests.get(f"{BASE_URL}/api/notes/{client_id}", headers=self.headers)
        assert notes_response.status_code == 200, f"Get notes failed: {notes_response.text}"
        
        notes = notes_response.json()
        assert len(notes) >= 1, "No notes found for client"
        
        # Find the initial comment note
        initial_note = next((n for n in notes if n["text"] == initial_comment), None)
        assert initial_note is not None, f"Initial comment not found in notes. Notes: {notes}"
        assert initial_note["client_id"] == client_id
        print(f"✓ Initial comment saved to notes collection: {initial_note['id']}")
    
    def test_create_client_with_reminder(self):
        """Test creating client with reminder_text and reminder_at - should create reminder"""
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        reminder_text = "Follow up with this client"
        reminder_at = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        
        payload = {
            "name": "TEST_Client With Reminder",
            "phone": phone,
            "source": "Telegram",
            "status": "new",
            "reminder_text": reminder_text,
            "reminder_at": reminder_at
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        print(f"✓ Created client with reminder: {client_id}")
        
        # Verify reminder was created
        reminders_response = requests.get(f"{BASE_URL}/api/reminders?include_completed=true", headers=self.headers)
        assert reminders_response.status_code == 200, f"Get reminders failed: {reminders_response.text}"
        
        reminders = reminders_response.json()
        # Find the reminder for this client
        client_reminder = next((r for r in reminders if r.get("client_id") == client_id), None)
        assert client_reminder is not None, f"Reminder not found for client {client_id}. Reminders: {reminders}"
        assert client_reminder["text"] == reminder_text
        assert client_reminder["is_completed"] == False
        print(f"✓ Reminder created in reminders collection: {client_reminder['id']}")
    
    def test_create_client_with_comment_and_reminder(self):
        """Test creating client with both initial_comment and reminder"""
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        initial_comment = "New lead from marketing campaign"
        reminder_text = "Call back tomorrow"
        reminder_at = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M")
        
        payload = {
            "name": "TEST_Client Full",
            "phone": phone,
            "source": "Website",
            "status": "new",
            "initial_comment": initial_comment,
            "reminder_text": reminder_text,
            "reminder_at": reminder_at
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        print(f"✓ Created client with comment and reminder: {client_id}")
        
        # Verify note
        notes_response = requests.get(f"{BASE_URL}/api/notes/{client_id}", headers=self.headers)
        notes = notes_response.json()
        assert any(n["text"] == initial_comment for n in notes), "Initial comment not found"
        print("✓ Initial comment verified")
        
        # Verify reminder
        reminders_response = requests.get(f"{BASE_URL}/api/reminders?include_completed=true", headers=self.headers)
        reminders = reminders_response.json()
        client_reminder = next((r for r in reminders if r.get("client_id") == client_id), None)
        assert client_reminder is not None, "Reminder not found"
        assert client_reminder["text"] == reminder_text
        print("✓ Reminder verified")
    
    def test_create_client_with_tariff(self):
        """Test creating client with tariff_id - should save tariff"""
        # First get available tariffs
        tariffs_response = requests.get(f"{BASE_URL}/api/tariffs", headers=self.headers)
        tariffs = tariffs_response.json()
        
        if not tariffs:
            # Create a test tariff
            tariff_response = requests.post(f"{BASE_URL}/api/tariffs", json={
                "name": "TEST_Tariff",
                "price": 100,
                "currency": "USD"
            }, headers=self.headers)
            tariff_id = tariff_response.json()["id"]
        else:
            tariff_id = tariffs[0]["id"]
        
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        payload = {
            "name": "TEST_Client With Tariff",
            "phone": phone,
            "source": "Referral",
            "status": "new",
            "tariff_id": tariff_id
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        assert data["tariff_id"] == tariff_id
        print(f"✓ Created client with tariff: {client_id}, tariff_id: {tariff_id}")
        
        # Verify tariff is returned when getting client
        get_response = requests.get(f"{BASE_URL}/api/clients/{client_id}", headers=self.headers)
        client_data = get_response.json()
        assert client_data["tariff_id"] == tariff_id
        print("✓ Tariff persisted correctly")
    
    def test_create_client_with_all_fields(self):
        """Test creating client with all new fields: tariff, comment, reminder"""
        # Get or create tariff
        tariffs_response = requests.get(f"{BASE_URL}/api/tariffs", headers=self.headers)
        tariffs = tariffs_response.json()
        tariff_id = tariffs[0]["id"] if tariffs else None
        
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        initial_comment = "VIP client from partner referral"
        reminder_text = "Schedule demo call"
        reminder_at = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        
        payload = {
            "name": "TEST_Full Client",
            "phone": phone,
            "source": "Partner",
            "status": "contacted",
            "tariff_id": tariff_id,
            "initial_comment": initial_comment,
            "reminder_text": reminder_text,
            "reminder_at": reminder_at
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        # Verify all fields
        assert data["name"] == "TEST_Full Client"
        assert data["status"] == "contacted"
        if tariff_id:
            assert data["tariff_id"] == tariff_id
        
        print(f"✓ Created client with all fields: {client_id}")
        
        # Verify note
        notes_response = requests.get(f"{BASE_URL}/api/notes/{client_id}", headers=self.headers)
        notes = notes_response.json()
        assert any(n["text"] == initial_comment for n in notes), "Initial comment not saved"
        print("✓ All fields verified")
    
    def test_create_client_reminder_without_text_ignored(self):
        """Test that reminder is not created if reminder_text is empty"""
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        reminder_at = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        
        payload = {
            "name": "TEST_No Reminder Text",
            "phone": phone,
            "source": "Test",
            "status": "new",
            "reminder_text": "",  # Empty text
            "reminder_at": reminder_at
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        # Verify no reminder was created for this client
        reminders_response = requests.get(f"{BASE_URL}/api/reminders?include_completed=true", headers=self.headers)
        reminders = reminders_response.json()
        client_reminder = next((r for r in reminders if r.get("client_id") == client_id), None)
        
        # Should be None since reminder_text was empty
        assert client_reminder is None, f"Reminder should not be created with empty text. Found: {client_reminder}"
        print(f"✓ No reminder created when reminder_text is empty")
    
    def test_create_client_empty_comment_not_saved(self):
        """Test that empty initial_comment is not saved as note"""
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        
        payload = {
            "name": "TEST_Empty Comment",
            "phone": phone,
            "source": "Test",
            "status": "new",
            "initial_comment": ""  # Empty comment
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Create client failed: {response.text}"
        
        data = response.json()
        client_id = data["id"]
        self.created_client_ids.append(client_id)
        
        # Verify no note was created
        notes_response = requests.get(f"{BASE_URL}/api/notes/{client_id}", headers=self.headers)
        notes = notes_response.json()
        
        # Should be empty since initial_comment was empty
        assert len(notes) == 0, f"No notes should be created with empty comment. Found: {notes}"
        print(f"✓ No note created when initial_comment is empty")


class TestClientUpdateDoesNotHaveCommentReminder:
    """Test that client update does NOT include comment/reminder fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create test client"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@crm.local",
            "password": "admin123"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Create a test client
        phone = f"+998{datetime.now().strftime('%H%M%S%f')[:9]}"
        response = requests.post(f"{BASE_URL}/api/clients", json={
            "name": "TEST_Update Client",
            "phone": phone,
            "status": "new"
        }, headers=self.headers)
        self.client_id = response.json()["id"]
        yield
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{self.client_id}", headers=self.headers)
    
    def test_update_client_does_not_accept_initial_comment(self):
        """Test that PUT /api/clients/{id} ignores initial_comment field"""
        # Try to update with initial_comment - should be ignored
        update_payload = {
            "name": "TEST_Updated Name",
            "initial_comment": "This should be ignored"
        }
        
        response = requests.put(f"{BASE_URL}/api/clients/{self.client_id}", 
                               json=update_payload, headers=self.headers)
        assert response.status_code == 200
        
        # Verify name was updated
        data = response.json()
        assert data["name"] == "TEST_Updated Name"
        
        # Verify no note was created from the update
        notes_response = requests.get(f"{BASE_URL}/api/notes/{self.client_id}", headers=self.headers)
        notes = notes_response.json()
        
        # Should have no notes since initial_comment in update should be ignored
        assert not any(n["text"] == "This should be ignored" for n in notes), \
            "initial_comment should not create note on update"
        print("✓ Update correctly ignores initial_comment field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
