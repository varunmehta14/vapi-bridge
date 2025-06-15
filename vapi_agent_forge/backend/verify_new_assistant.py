#!/usr/bin/env python3
"""
Verify the newly created assistant has tools properly embedded
"""

import asyncio
import sqlite3
from orchestrator import VapiOrchestrator

async def verify_new_assistant():
    """Verify the new assistant has tools properly embedded"""
    
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
    PUBLIC_SERVER_URL = "https://d6c5-2603-8000-baf0-4690-4c7d-38bd-11e8-5920.ngrok-free.app"
    orchestrator = VapiOrchestrator(vapi_api_key, PUBLIC_SERVER_URL)
    
    # The new assistant ID
    assistant_id = "48357f25-253f-48e1-bea5-dce97a25ca52"
    
    try:
        print(f"🔍 Verifying NEW assistant: {assistant_id}")
        
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
                
                # Show parameter details
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', 'No description')[:40]
                    print(f"          - {param_name} ({param_type}): {param_desc}...")
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
            print(f"   🎉 SUCCESS: Assistant has {len(tools)} tools!")
            print(f"\n🎯 TESTING INSTRUCTIONS:")
            print(f"   1. Go to VAPI Dashboard: https://dashboard.vapi.ai")
            print(f"   2. Find assistant: {assistant_id}")
            print(f"   3. Make a test call and try these queries:")
            print(f"      📞 'Research artificial intelligence trends'")
            print(f"      📞 'Create content about machine learning'") 
            print(f"      📞 'What is quantum computing?'")
            print(f"      📞 'Generate a summary about blockchain technology'")
            print(f"   4. Watch for tool calls in webhook logs")
            print(f"   5. Tools should trigger LangGraph Forge API calls")
        else:
            print(f"   ⚠️  WARNING: Expected 2 tools, found {len(tools)}")
            
    except Exception as e:
        print(f"❌ Error verifying assistant: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_new_assistant()) 