#!/usr/bin/env python3
import requests
import yaml
import json

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create voice agent with current configuration
config_yaml = yaml.dump(config, default_flow_style=False)
agent_data = {
    'name': 'Tools Verification Test',
    'config_yaml': config_yaml,
    'agent_type': 'verification'
}

print('🔍 Creating new voice agent to verify tools...')
response = requests.post('http://localhost:8000/users/4/voice-agents', json=agent_data)
print(f'Status: {response.status_code}')

if response.status_code == 200:
    result = response.json()
    print(f'✅ New Agent Created!')
    print(f'   Agent ID: {result["agent_id"]}')
    print(f'   VAPI Assistant ID: {result["vapi_assistant_id"]}')
    print(f'   Name: {result["name"]}')
    
    # Now check the VAPI assistant details
    assistant_id = result["vapi_assistant_id"]
    print(f'\n🔍 Checking VAPI assistant details for: {assistant_id}')
    
    # Get VAPI API key from database
    import sqlite3
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    cursor.execute("SELECT vapi_api_key FROM users WHERE id = ?", (4,))
    vapi_key_result = cursor.fetchone()
    conn.close()
    
    if vapi_key_result and vapi_key_result[0]:
        vapi_api_key = vapi_key_result[0]
        
        # Check the assistant via VAPI API
        vapi_response = requests.get(
            f'https://api.vapi.ai/assistant/{assistant_id}',
            headers={'Authorization': f'Bearer {vapi_api_key}'}
        )
        
        if vapi_response.status_code == 200:
            assistant_data = vapi_response.json()
            
            print(f'\n📋 VAPI Assistant Details:')
            print(f'   Name: {assistant_data.get("name")}')
            print(f'   Model: {assistant_data.get("model", {}).get("model")}')
            print(f'   Provider: {assistant_data.get("model", {}).get("provider")}')
            
            # Check tools
            tools = assistant_data.get("model", {}).get("tools", [])
            print(f'\n🔧 Tools Found: {len(tools)}')
            
            for i, tool in enumerate(tools, 1):
                tool_func = tool.get("function", {})
                print(f'   {i}. {tool_func.get("name", "Unknown")}')
                print(f'      Description: {tool_func.get("description", "No description")}')
                
                # Check parameters
                params = tool_func.get("parameters", {})
                properties = params.get("properties", {})
                required = params.get("required", [])
                
                print(f'      Parameters: {len(properties)} properties')
                for param_name, param_info in properties.items():
                    req_marker = " (required)" if param_name in required else ""
                    param_type = param_info.get("type", "unknown")
                    print(f'        - {param_name}: {param_type}{req_marker}')
                print()
            
            # Check server configuration
            server = assistant_data.get("server", {})
            if server:
                print(f'🌐 Webhook URL: {server.get("url", "Not set")}')
            
            print(f'\n✅ Tools verification complete!')
            print(f'   Expected tools: 2 (quick_research, quick_content)')
            print(f'   Found tools: {len(tools)}')
            
            if len(tools) == 2:
                tool_names = [tool.get("function", {}).get("name") for tool in tools]
                if "quick_research" in tool_names and "quick_content" in tool_names:
                    print(f'   ✅ All expected tools are present!')
                else:
                    print(f'   ⚠️ Tool names: {tool_names}')
            else:
                print(f'   ⚠️ Expected 2 tools, found {len(tools)}')
                
        else:
            print(f'❌ Failed to get VAPI assistant: {vapi_response.status_code} - {vapi_response.text}')
    else:
        print(f'❌ No VAPI API key found for user 4')
        
else:
    print(f'❌ Failed to create agent: {response.text}') 