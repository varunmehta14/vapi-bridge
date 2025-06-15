#!/usr/bin/env python3
"""
Debug assistant configuration to identify why tools aren't being called
"""

import asyncio
import sqlite3
import json
from orchestrator import VapiOrchestrator

async def debug_assistant():
    """Debug the assistant configuration to find why tools aren't working"""
    
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
    
    # The assistant ID that's not working
    assistant_id = "48357f25-253f-48e1-bea5-dce97a25ca52"
    
    try:
        print(f"🔍 DEBUGGING Assistant: {assistant_id}")
        
        # Get the full assistant configuration
        assistant = await orchestrator.get_assistant(assistant_id)
        
        print(f"\n📋 FULL ASSISTANT CONFIGURATION:")
        print(json.dumps(assistant, indent=2))
        
        # Check specific tool configuration
        tools = assistant.get('model', {}).get('tools', [])
        print(f"\n🔧 TOOL ANALYSIS:")
        print(f"   Tools found: {len(tools)}")
        
        if tools:
            for i, tool in enumerate(tools, 1):
                print(f"\n   Tool {i}:")
                print(f"     Type: {tool.get('type')}")
                print(f"     Function: {json.dumps(tool.get('function', {}), indent=6)}")
        
        # Check server configuration
        server = assistant.get('server', {})
        print(f"\n🌐 SERVER CONFIGURATION:")
        print(f"   URL: {server.get('url')}")
        print(f"   Timeout: {server.get('timeout')}")
        print(f"   Secret: {'***' if server.get('secret') else 'None'}")
        
        # Check model configuration
        model = assistant.get('model', {})
        print(f"\n🤖 MODEL CONFIGURATION:")
        print(f"   Provider: {model.get('provider')}")
        print(f"   Model: {model.get('model')}")
        print(f"   Messages: {len(model.get('messages', []))}")
        print(f"   Tools: {len(model.get('tools', []))}")
        
        # Check if tools are properly formatted
        print(f"\n🔍 TOOL VALIDATION:")
        for i, tool in enumerate(tools, 1):
            function = tool.get('function', {})
            name = function.get('name')
            description = function.get('description')
            parameters = function.get('parameters', {})
            
            print(f"   Tool {i} ({name}):")
            print(f"     ✅ Has name: {bool(name)}")
            print(f"     ✅ Has description: {bool(description)}")
            print(f"     ✅ Has parameters: {bool(parameters)}")
            print(f"     ✅ Parameters type: {parameters.get('type')}")
            print(f"     ✅ Has properties: {bool(parameters.get('properties'))}")
            print(f"     ✅ Has required: {bool(parameters.get('required'))}")
            
            if not all([name, description, parameters]):
                print(f"     ❌ ISSUE: Missing required fields!")
        
        # Compare with a working assistant (if we have one)
        print(f"\n🔄 COMPARISON WITH WORKING ASSISTANT:")
        
        # List all assistants to find a working one
        assistants_response = await orchestrator.list_assistants()
        assistants = assistants_response if isinstance(assistants_response, list) else assistants_response.get('data', [])
        
        # Find another assistant for comparison
        other_assistant = None
        for asst in assistants:
            if asst.get('id') != assistant_id and asst.get('name', '').startswith('LangGraph'):
                other_assistant = asst
                break
        
        if other_assistant:
            print(f"   Comparing with: {other_assistant.get('name')} ({other_assistant.get('id')})")
            
            # Get the other assistant's full config
            other_config = await orchestrator.get_assistant(other_assistant.get('id'))
            other_tools = other_config.get('model', {}).get('tools', [])
            
            print(f"   Other assistant tools: {len(other_tools)}")
            
            if other_tools and tools:
                print(f"   Tool structure comparison:")
                our_tool = tools[0]
                other_tool = other_tools[0]
                
                print(f"     Our tool keys: {list(our_tool.keys())}")
                print(f"     Other tool keys: {list(other_tool.keys())}")
                
                our_function = our_tool.get('function', {})
                other_function = other_tool.get('function', {})
                
                print(f"     Our function keys: {list(our_function.keys())}")
                print(f"     Other function keys: {list(other_function.keys())}")
        
        print(f"\n🎯 DIAGNOSIS:")
        if len(tools) == 0:
            print(f"   ❌ CRITICAL: No tools found in assistant!")
        elif not server.get('url'):
            print(f"   ❌ CRITICAL: No webhook URL configured!")
        elif not all(tool.get('function', {}).get('name') for tool in tools):
            print(f"   ❌ CRITICAL: Tools missing required fields!")
        else:
            print(f"   ✅ Configuration looks correct")
            print(f"   🤔 Issue might be:")
            print(f"      - VAPI not recognizing tools in voice calls")
            print(f"      - Model not triggering tool calls")
            print(f"      - Webhook URL not reachable from VAPI servers")
            print(f"      - Tool descriptions not clear enough for the model")
            
    except Exception as e:
        print(f"❌ Error debugging assistant: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_assistant()) 