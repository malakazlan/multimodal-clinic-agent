#!/usr/bin/env python3
"""
Simple API test script to verify endpoints are working.
Run this to test the API connectivity.
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")

def test_chat_endpoint():
    """Test the chat endpoint."""
    try:
        data = {
            "message": "Hello, how are you?",
            "conversation_id": "test-123",
            "user_id": "test-user"
        }
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Chat API: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Chat API failed: {e}")

def test_voice_transcribe_endpoint():
    """Test the voice transcribe endpoint."""
    try:
        # Create a simple test audio file (empty for testing)
        files = {"audio_file": ("test.wav", b"", "audio/wav")}
        response = requests.post(f"{BASE_URL}/api/voice/transcribe", files=files)
        print(f"Voice Transcribe API: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Voice transcribe API failed: {e}")

def test_frontend():
    """Test if the frontend is accessible."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Frontend: {response.status_code}")
        if response.status_code == 200:
            print("Frontend is accessible")
        else:
            print(f"Frontend error: {response.text[:200]}")
    except Exception as e:
        print(f"Frontend test failed: {e}")

if __name__ == "__main__":
    print("Testing Healthcare Voice AI Assistant API...")
    print("=" * 50)
    
    test_health_endpoint()
    print("-" * 30)
    
    test_frontend()
    print("-" * 30)
    
    test_chat_endpoint()
    print("-" * 30)
    
    test_voice_transcribe_endpoint()
    print("-" * 30)
    
    print("API testing complete!")
