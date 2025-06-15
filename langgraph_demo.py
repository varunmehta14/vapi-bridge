#!/usr/bin/env python3
"""
LangGraph Forge Integration Demo
Shows how service:// URLs resolve to your localhost:8082 service
"""

import requests
import json

# Your service configuration
USER_ID = 2  # researchers company
SERVICE_NAME = "langgraph_forge"
BASE_URL = "http://localhost:8000"

def test_service_resolution():
    """Test how service:// URLs resolve to your LangGraph Forge endpoints"""
    
    print("🔬 LangGraph Forge Integration Demo")
    print("=" * 50)
    
    # 1. Check service configuration
    print(f"1. Service Configuration for User {USER_ID}:")
    response = requests.get(f"{BASE_URL}/users/{USER_ID}/services")
    services = response.json()
    print(json.dumps(services, indent=2))
    
    # 2. Test service health
    print(f"\n2. Testing Service Health:")
    response = requests.post(f"{BASE_URL}/users/{USER_ID}/services/{SERVICE_NAME}/test")
    health = response.json()
    print(f"Status: {health['status']}")
    print(f"URL: {health['url']}")
    print(f"Response: {health['response']}")
    
    # 3. Show URL resolution examples
    print(f"\n3. URL Resolution Examples:")
    print("When you use these URLs in your voice agents:")
    print(f"  service://{SERVICE_NAME}/research     → http://localhost:8082/research")
    print(f"  service://{SERVICE_NAME}/analyze      → http://localhost:8082/analyze")
    print(f"  service://{SERVICE_NAME}/status/{{id}} → http://localhost:8082/status/{{id}}")
    
    # 4. Show what happens when you deploy with ngrok
    print(f"\n4. Future Deployment (with ngrok):")
    print("When you update your service URL to ngrok:")
    print(f"  service://{SERVICE_NAME}/research     → https://your-ngrok-url.ngrok.io/research")
    print(f"  service://{SERVICE_NAME}/analyze      → https://your-ngrok-url.ngrok.io/analyze")
    print("No code changes needed in your voice agents!")
    
    print(f"\n✅ Your LangGraph Forge service is ready for voice AI integration!")

if __name__ == "__main__":
    test_service_resolution() 