import requests
import time

# Test API endpoints
BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.status_code}")
    print(response.json())

def test_chat():
    response = requests.post(
        f"{BASE_URL}/chat/query",
        json={
            "query": "What security issues are in my code?",
            "session_id": "test-session-123"
        }
    )
    print(f"Chat Query: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    print("🧪 Testing Web API Functionality...")
    test_health()
    time.sleep(1)
    test_chat()
