#!/usr/bin/env python3

import json
import httpx
import asyncio

async def test_webhook():
    """Test the webhook endpoint directly"""
    
    # Test payload simulating a Vapi tool call
    test_payload = {
        "message": {
            "type": "tool-call",
            "toolCallList": [{
                "id": "test-123",
                "function": {
                    "name": "langgraph_quick_research",
                    "arguments": {
                        "query": "artificial intelligence"
                    }
                }
            }]
        }
    }
    
    print("🧪 Testing webhook endpoint...")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/webhook/tool-call",
                json=test_payload,
                timeout=30.0
            )
            
            print(f"📥 Status: {response.status_code}")
            print(f"📥 Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Webhook test successful!")
            else:
                print("❌ Webhook test failed!")
                
        except httpx.ConnectError:
            print("❌ Connection failed - is the FastAPI server running on localhost:8000?")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook()) 