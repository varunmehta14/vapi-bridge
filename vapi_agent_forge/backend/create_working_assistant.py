#!/usr/bin/env python3
"""
Create a working assistant using the existing ngrok tunnel
"""

import asyncio
import sqlite3
import json
from orchestrator import VapiOrchestrator

async def create_working_assistant():
    """Create an assistant that works with the current setup"""
    
    # Get VAPI API key from database
    try:
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vapi_api_key FROM users WHERE id = ?", (4,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            print("❌ No VAPI API key found for user 4")
            return
        
        vapi_api_key = result[0]
        print(f"✅ Found VAPI API key from database")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return
    
    # Use a different approach - create tools with server URLs pointing to localhost
    # and handle the routing in the webhook
    webhook_url = "https://d6c5-2603-8000-baf0-4690-4c7d-38bd-11e8-5920.ngrok-free.app"
    
    print(f"🚀 Creating assistant with webhook routing...")
    print(f"📡 Ngrok URL: {webhook_url}")
    print(f"🔄 Will route webhooks to localhost:8000")
    
    # Create orchestrator
    orchestrator = VapiOrchestrator(vapi_api_key, webhook_url)
    
    try:
        # Create an assistant
        user_id = "working_test"
        assistant = await orchestrator.create_assistant(user_id)
        
        if assistant:
            print(f"✅ Assistant created successfully!")
            print(f"   Assistant ID: {assistant.get('id')}")
            print(f"   Name: {assistant.get('name')}")
            print(f"   Webhook URL: {webhook_url}/webhook/tool-call")
            
            print(f"\n🎯 Setup Instructions:")
            print(f"   1. The tools are created with webhook: {webhook_url}/webhook/tool-call")
            print(f"   2. You need to add a webhook route to your LangGraph service")
            print(f"   3. Or modify the webhook URL to point to a working endpoint")
            
            print(f"\n🔧 Quick Fix Option:")
            print(f"   Run this command to test the assistant:")
            print(f"   curl -X POST {webhook_url}/webhook/tool-call -H 'Content-Type: application/json' -d '{{\"test\": \"data\"}}'")
            
            return assistant.get('id')
        else:
            print(f"❌ Failed to create assistant")
            return None
            
    except Exception as e:
        print(f"❌ Error creating assistant: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(create_working_assistant()) 