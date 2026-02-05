"""
Audio Upload, Streaming, and Delete API Tests
Tests the audio functionality including:
- Audio file upload
- Audio file listing for a client
- Audio streaming with JWT token (the fixed endpoint)
- Audio file deletion
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@crm.local"
TEST_PASSWORD = "admin123"
TEST_CLIENT_ID = "69842d991f067631f9c0d7dc"
EXISTING_AUDIO_ID = "69849224ebd60c51cf586fe1"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestAudioListing:
    """Test audio file listing endpoint"""
    
    def test_get_audio_files_for_client(self, api_client):
        """Test GET /api/audio/{client_id} returns audio files"""
        response = api_client.get(f"{BASE_URL}/api/audio/{TEST_CLIENT_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Should have at least one audio file
        if len(data) > 0:
            audio = data[0]
            assert "id" in audio
            assert "client_id" in audio
            assert "filename" in audio
            assert "original_name" in audio
            assert "content_type" in audio
            assert "size" in audio
            assert "uploader_name" in audio
            print(f"Found {len(data)} audio file(s) for client")
    
    def test_get_audio_files_requires_auth(self):
        """Test that audio listing requires authentication"""
        response = requests.get(f"{BASE_URL}/api/audio/{TEST_CLIENT_ID}")
        assert response.status_code == 403 or response.status_code == 401


class TestAudioStreaming:
    """Test audio streaming endpoint - THE FIXED ENDPOINT"""
    
    def test_stream_audio_with_token(self, auth_token):
        """Test GET /api/audio/stream/{audio_id}?token=... returns audio file"""
        response = requests.get(
            f"{BASE_URL}/api/audio/stream/{EXISTING_AUDIO_ID}?token={auth_token}",
            stream=True
        )
        
        assert response.status_code == 200, f"Streaming failed: {response.text}"
        assert response.headers.get("Content-Type") == "audio/wav"
        
        # Check Content-Length header
        content_length = response.headers.get("Content-Length")
        assert content_length is not None
        assert int(content_length) > 0
        print(f"Audio stream successful: {content_length} bytes, type: {response.headers.get('Content-Type')}")
    
    def test_stream_audio_without_token_fails(self):
        """Test that streaming without token returns 422 (missing required param)"""
        response = requests.get(f"{BASE_URL}/api/audio/stream/{EXISTING_AUDIO_ID}")
        # Should fail because token is required
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    def test_stream_audio_with_invalid_token_fails(self):
        """Test that streaming with invalid token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/audio/stream/{EXISTING_AUDIO_ID}?token=invalid_token"
        )
        assert response.status_code == 401
    
    def test_stream_nonexistent_audio_returns_404(self, auth_token):
        """Test that streaming non-existent audio returns 404"""
        fake_id = "000000000000000000000000"
        response = requests.get(
            f"{BASE_URL}/api/audio/stream/{fake_id}?token={auth_token}"
        )
        assert response.status_code == 404


class TestAudioUpload:
    """Test audio upload endpoint"""
    
    def test_upload_audio_file(self, auth_token):
        """Test POST /api/audio/upload uploads a file"""
        # Create a simple WAV file in memory (44 bytes header + 1 second of silence)
        wav_header = bytes([
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x00, 0x00, 0x00,  # File size - 8
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # Subchunk1Size (16)
            0x01, 0x00,              # AudioFormat (1 = PCM)
            0x01, 0x00,              # NumChannels (1)
            0x44, 0xAC, 0x00, 0x00,  # SampleRate (44100)
            0x88, 0x58, 0x01, 0x00,  # ByteRate
            0x02, 0x00,              # BlockAlign
            0x10, 0x00,              # BitsPerSample (16)
            0x64, 0x61, 0x74, 0x61,  # "data"
            0x00, 0x00, 0x00, 0x00,  # Subchunk2Size
        ])
        
        files = {
            'file': ('test_upload.wav', io.BytesIO(wav_header), 'audio/wav')
        }
        data = {
            'client_id': TEST_CLIENT_ID
        }
        
        response = requests.post(
            f"{BASE_URL}/api/audio/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        result = response.json()
        assert "id" in result
        assert result["client_id"] == TEST_CLIENT_ID
        assert result["original_name"] == "test_upload.wav"
        assert result["content_type"] == "audio/wav"
        
        # Store the ID for cleanup
        TestAudioUpload.uploaded_audio_id = result["id"]
        print(f"Uploaded audio file with ID: {result['id']}")
    
    def test_upload_invalid_file_type_fails(self, auth_token):
        """Test that uploading non-audio file fails"""
        files = {
            'file': ('test.txt', io.BytesIO(b'not an audio file'), 'text/plain')
        }
        data = {
            'client_id': TEST_CLIENT_ID
        }
        
        response = requests.post(
            f"{BASE_URL}/api/audio/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 400


class TestAudioDelete:
    """Test audio deletion endpoint"""
    
    def test_delete_audio_file(self, auth_token):
        """Test DELETE /api/audio/{audio_id} deletes the file"""
        # First upload a file to delete
        wav_header = bytes([
            0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00,
            0x57, 0x41, 0x56, 0x45, 0x66, 0x6D, 0x74, 0x20,
            0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
            0x44, 0xAC, 0x00, 0x00, 0x88, 0x58, 0x01, 0x00,
            0x02, 0x00, 0x10, 0x00, 0x64, 0x61, 0x74, 0x61,
            0x00, 0x00, 0x00, 0x00,
        ])
        
        files = {
            'file': ('to_delete.wav', io.BytesIO(wav_header), 'audio/wav')
        }
        data = {
            'client_id': TEST_CLIENT_ID
        }
        
        # Upload
        upload_response = requests.post(
            f"{BASE_URL}/api/audio/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files,
            data=data
        )
        assert upload_response.status_code == 200
        audio_id = upload_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/audio/{audio_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify it's gone
        stream_response = requests.get(
            f"{BASE_URL}/api/audio/stream/{audio_id}?token={auth_token}"
        )
        assert stream_response.status_code == 404
        print(f"Successfully deleted audio file {audio_id}")
    
    def test_delete_nonexistent_audio_returns_404(self, auth_token):
        """Test that deleting non-existent audio returns 404"""
        fake_id = "000000000000000000000000"
        response = requests.delete(
            f"{BASE_URL}/api/audio/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
