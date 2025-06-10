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
        Create a new Vapi assistant for a specific user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Created assistant data
        """
        config = self.load_config()
        assistant_config = config["assistant"]
        
        # First, create tools separately
        tool_ids = []
        for tool in config["tools"]:
            tool_data = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                },
                "server": {
                    "url": f"{self.public_server_url}/webhook/tool-call"
                }
            }
            
            # Create the tool via API
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/tool",
                        headers=self.headers,
                        json=tool_data,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    tool_result = response.json()
                    tool_ids.append(tool_result["id"])
                    print(f"✅ Created tool: {tool['name']} (ID: {tool_result['id']})")
                    
                except httpx.HTTPError as e:
                    print(f"⚠️  Failed to create tool {tool['name']}: {str(e)}")
                    # Continue with other tools
                    continue
        
        # Prepare the assistant configuration with shorter name
        assistant_name = f"Tesseract AI - {user_id[:10]}"  # Keep it under 40 chars
        vapi_assistant = {
            "name": assistant_name,
            "model": assistant_config["model"].copy(),
            "voice": assistant_config["voice"],
            "firstMessage": assistant_config["firstMessage"]
        }
        
        # Format system prompt with user_id
        if "system_prompt_template" in assistant_config["model"]:
            system_prompt = assistant_config["model"]["system_prompt_template"].format(user_id=user_id)
            vapi_assistant["model"]["systemPrompt"] = system_prompt
            # Remove the template field as Vapi expects systemPrompt
            del vapi_assistant["model"]["system_prompt_template"]
        
        # Add tool IDs to the model (not inline tools)
        if tool_ids:
            vapi_assistant["model"]["toolIds"] = tool_ids
        
        # Create the assistant via Vapi API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/assistant",
                    headers=self.headers,
                    json=vapi_assistant,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                # Get detailed error information
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_body = e.response.text
                        print(f"📋 Response status: {e.response.status_code}")
                        print(f"📋 Response body: {error_body}")
                    except:
                        pass
                raise Exception(f"Failed to create Vapi assistant: {str(e)}")
    
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
    
    async def update_assistant(self, assistant_id: str, user_id: str) -> Dict[str, Any]:
        """
        Update an existing assistant with new configuration
        
        Args:
            assistant_id: ID of the assistant to update  
            user_id: User ID for the assistant
            
        Returns:
            Updated assistant data
        """
        config = self.load_config()
        assistant_config = config["assistant"]
        
        # Prepare the updated configuration (same as create but as update)
        vapi_assistant = {
            "name": f"{assistant_config['name']} - {user_id}",
            "model": assistant_config["model"],
            "voice": assistant_config["voice"],
            "firstMessage": assistant_config["firstMessage"]
        }
        
        # Format system prompt with user_id
        if "system_prompt_template" in assistant_config["model"]:
            system_prompt = assistant_config["model"]["system_prompt_template"].format(user_id=user_id)
            vapi_assistant["model"]["systemPrompt"] = system_prompt
            del vapi_assistant["model"]["system_prompt_template"]
        
        # Convert tools to Vapi format
        vapi_tools = []
        for tool in config["tools"]:
            vapi_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            vapi_tools.append(vapi_tool)
        
        vapi_assistant["tools"] = vapi_tools
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/assistant/{assistant_id}",
                    headers=self.headers,
                    json=vapi_assistant,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                raise Exception(f"Failed to update assistant: {str(e)}")
    
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
    
    async def list_tools(self) -> Dict[str, Any]:
        """
        List all tools
        
        Returns:
            List of tools
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tool",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                raise Exception(f"Failed to list tools: {str(e)}")
                
    async def delete_tool(self, tool_id: str) -> bool:
        """
        Delete a tool
        
        Args:
            tool_id: ID of the tool to delete
            
        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/tool/{tool_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return True
                
            except httpx.HTTPError as e:
                raise Exception(f"Failed to delete tool: {str(e)}")

async def main():
    """
    Main function to demonstrate the orchestrator
    You'll need to set the VAPI_API_KEY and PUBLIC_SERVER_URL environment variables
    """
    # Get environment variables
    vapi_api_key = os.getenv("VAPI_API_KEY")
    public_server_url = os.getenv("PUBLIC_SERVER_URL", "https://your-ngrok-url.ngrok.io")
    
    if not vapi_api_key:
        print("❌ VAPI_API_KEY environment variable is required")
        print("   Set it with: export VAPI_API_KEY='your_vapi_api_key_here'")
        return
    
    if "localhost" in public_server_url:
        print("⚠️  Warning: PUBLIC_SERVER_URL appears to be localhost")
        print("   For Vapi webhooks to work, you need a public URL (ngrok)")
        print("   Set it with: export PUBLIC_SERVER_URL='https://your-ngrok-url.ngrok.io'")
    
    print(f"🚀 Initializing Vapi Orchestrator...")
    print(f"📡 Public Server URL: {public_server_url}")
    
    orchestrator = VapiOrchestrator(vapi_api_key, public_server_url)
    
    try:
        # Example: Create an assistant for a demo user
        print(f"\n🔨 Creating assistant for demo user...")
        user_id = "demo_user_123"
        assistant = await orchestrator.create_assistant(user_id)
        
        print(f"✅ Assistant created successfully!")
        print(f"   Assistant ID: {assistant.get('id')}")
        print(f"   Name: {assistant.get('name')}")
        
        # List all assistants
        print(f"\n📋 Listing all assistants...")
        assistants = await orchestrator.list_assistants()
        print(f"   Found {len(assistants)} assistant(s)")
        
        for asst in assistants:
            print(f"   - {asst.get('name')} (ID: {asst.get('id')})")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 