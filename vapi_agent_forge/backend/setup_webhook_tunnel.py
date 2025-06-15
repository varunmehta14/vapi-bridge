#!/usr/bin/env python3
"""
Setup script to help configure webhook tunnel for Vapi Agent Forge
"""

import asyncio
import sqlite3
import json
from orchestrator import VapiOrchestrator

async def create_assistant_with_webhook_url(webhook_url):
    """Create a new assistant with the specified webhook URL"""
    
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
    
    print(f"🚀 Creating assistant with webhook URL: {webhook_url}")
    
    # Create orchestrator with the webhook URL
    orchestrator = VapiOrchestrator(vapi_api_key, webhook_url)
    
    try:
        # Create an assistant
        user_id = "webhook_test"
        assistant = await orchestrator.create_assistant(user_id)
        
        if assistant:
            print(f"✅ Assistant created successfully!")
            print(f"   Assistant ID: {assistant.get('id')}")
            print(f"   Name: {assistant.get('name')}")
            print(f"   Webhook URL: {webhook_url}/webhook/tool-call")
            
            print(f"\n🎯 Next Steps:")
            print(f"   1. Go to VAPI Dashboard: https://dashboard.vapi.ai")
            print(f"   2. Find assistant: {assistant.get('id')}")
            print(f"   3. Test with voice calls")
            print(f"   4. Tools will call: {webhook_url}/webhook/tool-call")
            
            return assistant.get('id')
        else:
            print(f"❌ Failed to create assistant")
            return None
            
    except Exception as e:
        print(f"❌ Error creating assistant: {str(e)}")
        return None

def main():
    print("🔧 Vapi Agent Forge Webhook Setup")
    print("=" * 50)
    
    print("\n📋 Instructions:")
    print("1. Open a new terminal")
    print("2. Run: ngrok http 8000")
    print("3. Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)")
    print("4. Paste it below")
    
    webhook_url = input("\n🌐 Enter your ngrok URL for port 8000: ").strip()
    
    if not webhook_url:
        print("❌ No URL provided")
        return
    
    if not webhook_url.startswith('https://'):
        print("❌ URL must start with https://")
        return
    
    if webhook_url.endswith('/'):
        webhook_url = webhook_url[:-1]
    
    print(f"\n✅ Using webhook URL: {webhook_url}")
    
    # Create assistant with the webhook URL
    assistant_id = asyncio.run(create_assistant_with_webhook_url(webhook_url))
    
    if assistant_id:
        print(f"\n🎉 SUCCESS!")
        print(f"Assistant ID: {assistant_id}")
        print(f"Ready for voice calls!")
    else:
        print(f"\n❌ FAILED to create assistant")

if __name__ == "__main__":
    main() 