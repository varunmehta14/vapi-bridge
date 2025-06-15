#!/usr/bin/env python3
"""
Verify that the assistant was created with tools properly embedded
"""

import asyncio
import sqlite3
from orchestrator import VapiOrchestrator

async def verify_assistant():
    """Verify the assistant has tools properly embedded"""
    
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
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return
    
    # Initialize orchestrator
    PUBLIC_SERVER_URL = "https://845f-2603-8000-baf0-4690-4c7d-38bd-11e8-5920.ngrok-free.app"
    orchestrator = VapiOrchestrator(vapi_api_key, PUBLIC_SERVER_URL)
    
    # The assistant ID from the previous creation
    assistant_id = "7290706e-271d-4a44-934e-d353f97f8710"
    
    try:
        print(f"🔍 Verifying assistant: {assistant_id}")
        
        # Get the assistant details
        assistant = await orchestrator.get_assistant(assistant_id)
        
        print(f"✅ Assistant Details:")
        print(f"   ID: {assistant.get('id')}")
        print(f"   Name: {assistant.get('name')}")
        print(f"   Model: {assistant.get('model', {}).get('model')}")
        print(f"   Provider: {assistant.get('model', {}).get('provider')}")
        
        # Check tools
        tools = assistant.get('model', {}).get('tools', [])
        print(f"   Tools: {len(tools)} found")
        
        if tools:
            print(f"   📋 Tool Details:")
            for i, tool in enumerate(tools, 1):
                function = tool.get('function', {})
                print(f"     {i}. {function.get('name', 'Unknown')}")
                print(f"        Type: {tool.get('type')}")
                print(f"        Description: {function.get('description', 'No description')[:60]}...")
                
                # Check parameters
                params = function.get('parameters', {})
                properties = params.get('properties', {})
                required = params.get('required', [])
                
                print(f"        Parameters: {len(properties)} properties")
                print(f"        Required: {required}")
        else:
            print(f"   ❌ No tools found in assistant!")
        
        # Check voice configuration
        voice = assistant.get('voice', {})
        print(f"   Voice Provider: {voice.get('provider')}")
        print(f"   Voice ID: {voice.get('voiceId')}")
        
        # Check server configuration
        server = assistant.get('server', {})
        print(f"   Webhook URL: {server.get('url')}")
        
        print(f"\n🎯 Verification Summary:")
        print(f"   ✅ Assistant exists: {assistant.get('id') is not None}")
        print(f"   ✅ Has tools: {len(tools) > 0}")
        print(f"   ✅ Tools in model: {len(tools)} tools found")
        print(f"   ✅ Webhook configured: {server.get('url') is not None}")
        
        if len(tools) >= 2:
            print(f"   🎉 SUCCESS: Assistant has {len(tools)} tools - should be visible in dashboard!")
        else:
            print(f"   ⚠️  WARNING: Expected 2 tools, found {len(tools)}")
            
    except Exception as e:
        print(f"❌ Error verifying assistant: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_assistant()) 