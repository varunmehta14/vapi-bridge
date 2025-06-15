#!/usr/bin/env python3
"""
Vapi Assistant Orchestrator

This script programmatically creates and manages Vapi assistants using the configuration
defined in config.yaml. It handles the creation of assistants with proper webhook URLs.
"""

import os
import json
import asyncio
import httpx
from typing import Dict, Any, Optional
import yaml
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VapiOrchestrator:
    """Handles creation and management of Vapi assistants"""
    
    def __init__(self, vapi_api_key: str, public_server_url: str):
        self.vapi_api_key = vapi_api_key
        self.public_server_url = public_server_url
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {vapi_api_key}",
            "Content-Type": "application/json"
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml"""
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file)
    
    async def create_assistant(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new Vapi assistant for a specific user using the working approach
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Created assistant data
        """
        config = self.load_config()
        assistant_config = config["assistant"]
        tools_config = config["tools"]
        
        print(f"✅ Loaded config with {len(tools_config)} tools")
        
        # Convert our YAML tools to Vapi format (exactly like the working example)
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
        
        # Create Vapi assistant configuration (exactly like the working example)
        vapi_assistant_config = {
            "name": assistant_config["name"],
            "model": {
                "provider": assistant_config["model"]["provider"],
                "model": assistant_config["model"]["model"],
                "messages": [{
                    "role": "system",
                    "content": assistant_config["model"].get("system_prompt_template", "You are a helpful AI assistant.")
                }],
                "tools": vapi_tools  # Tools inside model object
            },
            "voice": assistant_config["voice"],
            "firstMessage": assistant_config["firstMessage"],
            "server": {
                "url": f"{self.public_server_url}/webhook/tool-call"
            }
        }
        
        print(f"🔍 VAPI Assistant Config:")
        print(f"   Name: {vapi_assistant_config['name']}")
        print(f"   Model: {vapi_assistant_config['model']['model']}")
        print(f"   Tools: {len(vapi_assistant_config['model']['tools'])}")
        print(f"   Webhook: {vapi_assistant_config['server']['url']}")
        
        # Create the assistant via Vapi API (exactly like the working example)
        async with httpx.AsyncClient() as client:
            try:
                print(f"🚀 Creating VAPI assistant...")
                response = await client.post(
                    f"{self.base_url}/assistant",
                    headers=self.headers,
                    json=vapi_assistant_config,
                    timeout=30.0
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
    
    async def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """
        Get an existing assistant by ID
        
        Args:
            assistant_id: ID of the assistant to retrieve
            
        Returns:
            Assistant data
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/assistant/{assistant_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                raise Exception(f"Failed to get assistant: {str(e)}")
    
    async def list_assistants(self) -> Dict[str, Any]:
        """
        List all assistants
        
        Returns:
            List of assistants
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/assistant",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                raise Exception(f"Failed to list assistants: {str(e)}")
    
    async def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant
        
        Args:
            assistant_id: ID of the assistant to delete
            
        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/assistant/{assistant_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return True
                
            except httpx.HTTPError as e:
                raise Exception(f"Failed to delete assistant: {str(e)}")

async def main():
    """
    Main function to demonstrate the orchestrator
    Uses database to get VAPI API key like the working example
    """
    # Set PUBLIC_SERVER_URL
    PUBLIC_SERVER_URL = "https://ba54-2603-8000-ba00-34c9-2046-d24b-6925-bbb0.ngrok-free.app"
    
    # Get VAPI API key from database (like the working example)
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
    
    print(f"🚀 Initializing Vapi Orchestrator...")
    print(f"📡 Public Server URL: {PUBLIC_SERVER_URL}")
    
    orchestrator = VapiOrchestrator(vapi_api_key, PUBLIC_SERVER_URL)
    
    try:
        # Create an assistant for a demo user
        print(f"\n🔨 Creating assistant...")
        user_id = "orchestrator_test"
        assistant = await orchestrator.create_assistant(user_id)
        
        if assistant:
            print(f"✅ Assistant created successfully!")
            print(f"   Assistant ID: {assistant.get('id')}")
            print(f"   Name: {assistant.get('name')}")
            
            # Verify tools were created
            tools = assistant.get("model", {}).get("tools", [])
            print(f"   Tools created: {len(tools)}")
            
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get("function", {}).get("name", "Unknown")
                print(f"     {i}. {tool_name}")
            
            print(f"\n🎯 Check VAPI Dashboard:")
            print(f"   Go to: https://dashboard.vapi.ai")
            print(f"   Find assistant: {assistant.get('id')}")
            print(f"   You should see {len(tools)} tools!")
        
        # List all assistants
        print(f"\n📋 Listing all assistants...")
        assistants_response = await orchestrator.list_assistants()
        assistants = assistants_response if isinstance(assistants_response, list) else assistants_response.get('data', [])
        print(f"   Found {len(assistants)} assistant(s)")
        
        for asst in assistants:
            print(f"   - {asst.get('name')} (ID: {asst.get('id')})")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 