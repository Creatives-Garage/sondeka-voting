#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Skiza Audio Player
Tests all backend endpoints including audio upload, streaming, and playlist management
"""

import requests
import json
import io
import os
import time
from pathlib import Path

# Backend URL from frontend/.env
BACKEND_URL = "https://dada0df0-b7fc-41bb-b661-85cc1eed6d6d.preview.emergentagent.com/api"

class SkizaBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.uploaded_audio_id = None
        self.created_playlist_id = None
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def test_health_endpoints(self):
        """Test basic health check endpoints"""
        print("\n=== Testing Health Endpoints ===")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Skiza" in data["message"]:
                    self.log_test("GET /api/", True, f"Response: {data}")
                else:
                    self.log_test("GET /api/", False, f"Unexpected response: {data}")
            else:
                self.log_test("GET /api/", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("GET /api/", False, f"Exception: {str(e)}")
            
        # Test health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("GET /api/health", True, f"Response: {data}")
                else:
                    self.log_test("GET /api/health", False, f"Unexpected response: {data}")
            else:
                self.log_test("GET /api/health", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("GET /api/health", False, f"Exception: {str(e)}")
    
    def create_test_audio_file(self):
        """Create a small test audio file in memory"""
        # Create a minimal WAV file (44 bytes header + some data)
        wav_header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        # Add some audio data (silence)
        audio_data = b'\x00' * 1000
        return wav_header + audio_data
    
    def test_audio_upload(self):
        """Test audio file upload functionality"""
        print("\n=== Testing Audio Upload ===")
        
        try:
            # Create test audio file
            audio_content = self.create_test_audio_file()
            
            # Prepare multipart form data
            files = {
                'file': ('test_song.wav', io.BytesIO(audio_content), 'audio/wav')
            }
            data = {
                'title': 'Test Song for Skiza Player',
                'artist': 'Test Artist',
                'duration': 30.5,
                'is_podcast': False
            }
            
            response = self.session.post(f"{self.base_url}/upload-audio", files=files, data=data)
            
            if response.status_code == 200:
                audio_metadata = response.json()
                if 'id' in audio_metadata and 'title' in audio_metadata:
                    self.uploaded_audio_id = audio_metadata['id']
                    self.log_test("POST /api/upload-audio", True, f"Uploaded audio ID: {self.uploaded_audio_id}")
                    self.log_test("Audio Metadata Storage", True, f"Metadata: {json.dumps(audio_metadata, indent=2)}")
                else:
                    self.log_test("POST /api/upload-audio", False, f"Missing required fields in response: {audio_metadata}")
            else:
                self.log_test("POST /api/upload-audio", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/upload-audio", False, f"Exception: {str(e)}")
    
    def test_invalid_file_upload(self):
        """Test upload with invalid file type"""
        print("\n=== Testing Invalid File Upload ===")
        
        try:
            # Create a text file instead of audio
            text_content = b"This is not an audio file"
            
            files = {
                'file': ('test.txt', io.BytesIO(text_content), 'text/plain')
            }
            data = {
                'title': 'Invalid File Test',
                'artist': 'Test Artist'
            }
            
            response = self.session.post(f"{self.base_url}/upload-audio", files=files, data=data)
            
            if response.status_code == 400:
                self.log_test("Invalid File Upload Validation", True, "Correctly rejected non-audio file")
            else:
                self.log_test("Invalid File Upload Validation", False, f"Expected 400, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Invalid File Upload Validation", False, f"Exception: {str(e)}")
    
    def test_get_all_audio(self):
        """Test getting all audio files"""
        print("\n=== Testing Get All Audio Files ===")
        
        try:
            response = self.session.get(f"{self.base_url}/audio")
            
            if response.status_code == 200:
                audio_files = response.json()
                if isinstance(audio_files, list):
                    self.log_test("GET /api/audio", True, f"Retrieved {len(audio_files)} audio files")
                    if self.uploaded_audio_id and any(audio['id'] == self.uploaded_audio_id for audio in audio_files):
                        self.log_test("Audio List Contains Uploaded File", True, "Uploaded file found in list")
                    elif self.uploaded_audio_id:
                        self.log_test("Audio List Contains Uploaded File", False, "Uploaded file not found in list")
                else:
                    self.log_test("GET /api/audio", False, f"Expected list, got: {type(audio_files)}")
            else:
                self.log_test("GET /api/audio", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/audio", False, f"Exception: {str(e)}")
    
    def test_get_specific_audio(self):
        """Test getting specific audio file metadata"""
        print("\n=== Testing Get Specific Audio File ===")
        
        if not self.uploaded_audio_id:
            self.log_test("GET /api/audio/{id}", False, "No uploaded audio ID available for testing")
            return
            
        try:
            response = self.session.get(f"{self.base_url}/audio/{self.uploaded_audio_id}")
            
            if response.status_code == 200:
                audio_metadata = response.json()
                if audio_metadata.get('id') == self.uploaded_audio_id:
                    self.log_test("GET /api/audio/{id}", True, f"Retrieved metadata for audio {self.uploaded_audio_id}")
                else:
                    self.log_test("GET /api/audio/{id}", False, f"ID mismatch: expected {self.uploaded_audio_id}, got {audio_metadata.get('id')}")
            else:
                self.log_test("GET /api/audio/{id}", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/audio/{id}", False, f"Exception: {str(e)}")
    
    def test_audio_streaming(self):
        """Test audio file streaming"""
        print("\n=== Testing Audio Streaming ===")
        
        if not self.uploaded_audio_id:
            self.log_test("GET /api/audio/{id}/stream", False, "No uploaded audio ID available for testing")
            return
            
        try:
            response = self.session.get(f"{self.base_url}/audio/{self.uploaded_audio_id}/stream")
            
            if response.status_code == 200:
                # Check headers
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '')
                accept_ranges = response.headers.get('accept-ranges', '')
                
                if content_type.startswith('audio/'):
                    self.log_test("Audio Streaming Headers", True, f"Content-Type: {content_type}, Length: {content_length}")
                else:
                    self.log_test("Audio Streaming Headers", False, f"Invalid content-type: {content_type}")
                
                # Check if we can read some content
                content = response.content
                if len(content) > 0:
                    self.log_test("GET /api/audio/{id}/stream", True, f"Streamed {len(content)} bytes")
                else:
                    self.log_test("GET /api/audio/{id}/stream", False, "No content received")
            else:
                self.log_test("GET /api/audio/{id}/stream", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/audio/{id}/stream", False, f"Exception: {str(e)}")
    
    def test_playlist_creation(self):
        """Test playlist creation"""
        print("\n=== Testing Playlist Creation ===")
        
        try:
            playlist_data = {
                'title': 'My Awesome Skiza Playlist',
                'audio_items': [self.uploaded_audio_id] if self.uploaded_audio_id else []
            }
            
            response = self.session.post(f"{self.base_url}/playlists", json=playlist_data)
            
            if response.status_code == 200:
                playlist = response.json()
                if 'id' in playlist and 'title' in playlist:
                    self.created_playlist_id = playlist['id']
                    self.log_test("POST /api/playlists", True, f"Created playlist ID: {self.created_playlist_id}")
                else:
                    self.log_test("POST /api/playlists", False, f"Missing required fields: {playlist}")
            else:
                self.log_test("POST /api/playlists", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/playlists", False, f"Exception: {str(e)}")
    
    def test_get_all_playlists(self):
        """Test getting all playlists"""
        print("\n=== Testing Get All Playlists ===")
        
        try:
            response = self.session.get(f"{self.base_url}/playlists")
            
            if response.status_code == 200:
                playlists = response.json()
                if isinstance(playlists, list):
                    self.log_test("GET /api/playlists", True, f"Retrieved {len(playlists)} playlists")
                    if self.created_playlist_id and any(playlist['id'] == self.created_playlist_id for playlist in playlists):
                        self.log_test("Playlist List Contains Created Playlist", True, "Created playlist found in list")
                    elif self.created_playlist_id:
                        self.log_test("Playlist List Contains Created Playlist", False, "Created playlist not found in list")
                else:
                    self.log_test("GET /api/playlists", False, f"Expected list, got: {type(playlists)}")
            else:
                self.log_test("GET /api/playlists", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/playlists", False, f"Exception: {str(e)}")
    
    def test_get_specific_playlist(self):
        """Test getting specific playlist"""
        print("\n=== Testing Get Specific Playlist ===")
        
        if not self.created_playlist_id:
            self.log_test("GET /api/playlists/{id}", False, "No created playlist ID available for testing")
            return
            
        try:
            response = self.session.get(f"{self.base_url}/playlists/{self.created_playlist_id}")
            
            if response.status_code == 200:
                playlist = response.json()
                if playlist.get('id') == self.created_playlist_id:
                    self.log_test("GET /api/playlists/{id}", True, f"Retrieved playlist {self.created_playlist_id}")
                else:
                    self.log_test("GET /api/playlists/{id}", False, f"ID mismatch: expected {self.created_playlist_id}, got {playlist.get('id')}")
            else:
                self.log_test("GET /api/playlists/{id}", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/playlists/{id}", False, f"Exception: {str(e)}")
    
    def test_delete_audio(self):
        """Test audio file deletion"""
        print("\n=== Testing Audio Deletion ===")
        
        if not self.uploaded_audio_id:
            self.log_test("DELETE /api/audio/{id}", False, "No uploaded audio ID available for testing")
            return
            
        try:
            response = self.session.delete(f"{self.base_url}/audio/{self.uploaded_audio_id}")
            
            if response.status_code == 200:
                result = response.json()
                if "deleted" in result.get("message", "").lower():
                    self.log_test("DELETE /api/audio/{id}", True, f"Deleted audio {self.uploaded_audio_id}")
                    
                    # Verify deletion by trying to get the file
                    verify_response = self.session.get(f"{self.base_url}/audio/{self.uploaded_audio_id}")
                    if verify_response.status_code == 404:
                        self.log_test("Audio Deletion Verification", True, "Audio file no longer accessible after deletion")
                    else:
                        self.log_test("Audio Deletion Verification", False, f"Audio still accessible after deletion: {verify_response.status_code}")
                else:
                    self.log_test("DELETE /api/audio/{id}", False, f"Unexpected response: {result}")
            else:
                self.log_test("DELETE /api/audio/{id}", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("DELETE /api/audio/{id}", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for non-existent resources"""
        print("\n=== Testing Error Handling ===")
        
        # Test getting non-existent audio file
        try:
            response = self.session.get(f"{self.base_url}/audio/non-existent-id")
            if response.status_code == 404:
                self.log_test("Non-existent Audio Error Handling", True, "Correctly returned 404 for non-existent audio")
            else:
                self.log_test("Non-existent Audio Error Handling", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Audio Error Handling", False, f"Exception: {str(e)}")
        
        # Test getting non-existent playlist
        try:
            response = self.session.get(f"{self.base_url}/playlists/non-existent-id")
            if response.status_code == 404:
                self.log_test("Non-existent Playlist Error Handling", True, "Correctly returned 404 for non-existent playlist")
            else:
                self.log_test("Non-existent Playlist Error Handling", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Playlist Error Handling", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🎵 Starting Skiza Audio Player Backend API Tests 🎵")
        print(f"Testing backend at: {self.base_url}")
        
        # Test in logical order
        self.test_health_endpoints()
        self.test_audio_upload()
        self.test_invalid_file_upload()
        self.test_get_all_audio()
        self.test_get_specific_audio()
        self.test_audio_streaming()
        self.test_playlist_creation()
        self.test_get_all_playlists()
        self.test_get_specific_playlist()
        self.test_error_handling()
        self.test_delete_audio()  # Delete last to clean up
        
        print("\n🎵 Backend API Testing Complete 🎵")

if __name__ == "__main__":
    tester = SkizaBackendTester()
    tester.run_all_tests()