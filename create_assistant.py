#!/usr/bin/env python3
"""
Simple script to create a Vapi assistant with the current configuration
"""

import os
import json
import requests
import yaml

# Configuration
VAPI_API_KEY = os.getenv('VAPI_API_KEY')
PUBLIC_SERVER_URL = os.getenv('PUBLIC_SERVER_URL', 'https://ba54-2603-8000-ba00-34c9-2046-d24b-6925-bbb0.ngrok-free.app')
BACKEND_URL = "http://localhost:8000"

def load_yaml_config():
    """Load the YAML configuration"""
    with open('langgraph_voice_optimized.yaml', 'r') as file:
        return yaml.safe_load(file)

def create_vapi_assistant():
    """Create a Vapi assistant using the loaded configuration"""
    if not VAPI_API_KEY:
        print("❌ VAPI_API_KEY environment variable not set")
        return None
    
    # Load configuration
    config = load_yaml_config()
    assistant_config = config["assistant"]
    tools_config = config["tools"]
    
    print(f"✅ Loaded config with {len(tools_config)} tools")
    print(f"🔍 Using ngrok URL: {PUBLIC_SERVER_URL}")
    
    # Convert tools to Vapi format
    vapi_tools = []
    for tool in tools_config:
        vapi_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        }
        vapi_tools.append(vapi_tool)
    
    print(f"✅ Converted {len(vapi_tools)} tools to VAPI format")
    
    # Create assistant configuration
    vapi_assistant_config = {
        "name": assistant_config["name"],
        "model": {
            "provider": assistant_config["model"]["provider"],
            "model": assistant_config["model"]["model"],
            "messages": [{
                "role": "system",
                "content": assistant_config["model"]["system_prompt_template"]
            }],
            "tools": vapi_tools
        },
        "voice": assistant_config["voice"],
        "firstMessage": assistant_config["firstMessage"],
        "server": {
            "url": f"{PUBLIC_SERVER_URL}/webhook/tool-call"
        }
    }
    
    print(f"🔍 VAPI Assistant Config:")
    print(f"   Name: {vapi_assistant_config['name']}")
    print(f"   Model: {vapi_assistant_config['model']['model']}")
    print(f"   Tools: {len(vapi_assistant_config['model']['tools'])}")
    print(f"   Webhook: {vapi_assistant_config['server']['url']}")
    
    # Create via Vapi API
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🚀 Creating VAPI assistant...")
        response = requests.post(
            "https://api.vapi.ai/assistant",
            headers=headers,
            json=vapi_assistant_config,
            timeout=30
        )
        
        print(f"📡 VAPI API Response: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            
            print(f"✅ SUCCESS! Assistant created:")
            print(f"   Assistant ID: {result['id']}")
            print(f"   Name: {result['name']}")
            
            # Verify tools were created
            tools = result.get("model", {}).get("tools", [])
            print(f"   Tools created: {len(tools)}")
            
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get("function", {}).get("name", "Unknown")
                print(f"     {i}. {tool_name}")
            
            return result
            
        else:
            print(f"❌ VAPI API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 Creating Vapi Assistant with LangGraph Integration")
    print("="*60)
    
    if not VAPI_API_KEY:
        print("❌ Please set your VAPI_API_KEY environment variable")
        exit(1)
    
    result = create_vapi_assistant()
    
    if result:
        print("\n" + "="*60)
        print("✅ Assistant creation successful!")
        print(f"🎯 Assistant ID: {result['id']}")
        print(f"📞 You can now make voice calls to this assistant")
        print("="*60)
    else:
        print("\n❌ Assistant creation failed")
        exit(1) 