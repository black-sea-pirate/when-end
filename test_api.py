"""
Simple API test script to verify backend is working.
Run: python test_api.py
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:3000/api"

def test_health():
    """Test health endpoint."""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_auth_flow():
    """Test authentication flow (without actual Google OAuth)."""
    print("\n🔍 Testing auth endpoints...")
    try:
        # Try to get current user (should fail without auth)
        response = requests.get(f"{BASE_URL}/auth/me")
        if response.status_code == 401:
            print("✅ Auth protection working (401 for unauthenticated)")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_event_creation_without_auth():
    """Test that event creation requires authentication."""
    print("\n🔍 Testing event creation without auth...")
    try:
        event_data = {
            "title": "Test Event",
            "description": "This should fail",
            "event_date": (datetime.now() + timedelta(days=1)).isoformat() + "Z",
            "repeat_interval": "none"
        }
        response = requests.post(
            f"{BASE_URL}/events",
            json=event_data
        )
        if response.status_code == 401:
            print("✅ Event creation requires auth (401)")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("  when-end API Test Suite")
    print("=" * 60)
    
    print("\n📡 Testing backend at:", BASE_URL)
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health()))
    
    # Test auth
    results.append(("Auth Protection", test_auth_flow()))
    
    # Test event creation
    results.append(("Event Auth Check", test_event_creation_without_auth()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Configure Google OAuth in .env")
        print("   2. Sign in at http://localhost:3000")
        print("   3. Create your first countdown event!")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("   1. Is Docker running?")
        print("   2. Are all containers up? (docker compose ps)")
        print("   3. Check logs: docker compose logs backend")


if __name__ == "__main__":
    main()
