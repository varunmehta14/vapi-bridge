#!/usr/bin/env python3
"""
Create assistant using webhook proxy approach
"""

import asyncio
import sqlite3
from orchestrator import VapiOrchestrator

async def create_proxy_assistant():
    """Create assistant using webhook proxy"""
    
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
    
    # You'll need to get the ngrok URL for port 8083
    webhook_proxy_url = input("🌐 Enter ngrok URL for port 8083 (e.g., https://abc123.ngrok-free.app): ").strip()
    
    if not webhook_proxy_url:
        print("❌ No URL provided")
        return
    
    if webhook_proxy_url.endswith('/'):
        webhook_proxy_url = webhook_proxy_url[:-1]
    
    print(f"🚀 Creating assistant with webhook proxy: {webhook_proxy_url}")
    
    # Create orchestrator with webhook proxy URL
    orchestrator = VapiOrchestrator(vapi_api_key, webhook_proxy_url)
    
    try:
        # Create an assistant
        user_id = "proxy_test"
        assistant = await orchestrator.create_assistant(user_id)
        
        if assistant:
            print(f"✅ Assistant created successfully!")
            print(f"   Assistant ID: {assistant.get('id')}")
            print(f"   Name: {assistant.get('name')}")
            print(f"   Webhook URL: {webhook_proxy_url}/webhook/tool-call")
            
            print(f"\n🎯 Flow:")
            print(f"   Vapi → {webhook_proxy_url}/webhook/tool-call")
            print(f"   Proxy → http://localhost:8000/webhook/tool-call")
            print(f"   Backend → LangGraph APIs → Response")
            
            return assistant.get('id')
        else:
            print(f"❌ Failed to create assistant")
            return None
            
    except Exception as e:
        print(f"❌ Error creating assistant: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(create_proxy_assistant()) 