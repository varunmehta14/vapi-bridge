#!/usr/bin/env python3
"""
Script to create a voice agent from YAML configuration
Usage: python create_agent_from_yaml.py student_research_assistant_v3.yaml
"""

import yaml
import requests
import json
import sys
from typing import Dict, Any

def load_yaml_config(yaml_file: str) -> Dict[str, Any]:
    """Load and parse YAML configuration file."""
    try:
        with open(yaml_file, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: YAML file '{yaml_file}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

def create_voice_agent(config: Dict[str, Any]) -> Dict[str, Any]:
    """Create voice agent using the backend API."""
    
    agent_config = config['agent_config']
    
    # Prepare the payload for the API
    payload = {
        "name": agent_config['name'],
        "description": agent_config['description'],
        "user_id": agent_config['user_id'],
        "user_email": agent_config['user_email'],
        
        # Voice settings
        "voice_provider": agent_config['voice']['provider'],
        "voice_id": agent_config['voice']['voice_id'],
        "voice_speed": agent_config['voice']['speed'],
        "voice_stability": agent_config['voice']['stability'],
        "voice_similarity_boost": agent_config['voice']['similarity_boost'],
        
        # Model settings
        "model_provider": agent_config['model']['provider'],
        "model_name": agent_config['model']['name'],
        "temperature": agent_config['model']['temperature'],
        "max_tokens": agent_config['model']['max_tokens'],
        
        # System prompt
        "system_prompt": agent_config['system_prompt'],
        
        # Webhook
        "webhook_url": agent_config['webhook']['url'],
        
        # Conversation settings
        "max_duration_seconds": agent_config['conversation']['max_duration_seconds'],
        "silence_timeout_seconds": agent_config['conversation']['silence_timeout_seconds'],
        
        # Tools
        "tools": agent_config['tools']
    }
    
    # API endpoint
    api_url = "http://localhost:8000/api/agents"
    
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_agent_from_yaml.py <yaml_file>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    
    print(f"Loading configuration from {yaml_file}...")
    config = load_yaml_config(yaml_file)
    
    print("Creating voice agent...")
    result = create_voice_agent(config)
    
    print("✅ Voice agent created successfully!")
    print(f"Agent ID: {result.get('agent_id')}")
    print(f"Vapi Assistant ID: {result.get('vapi_assistant_id')}")
    print(f"Phone Number: {result.get('phone_number', 'Not assigned')}")
    
    # Save result to file
    with open('agent_creation_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("Result saved to agent_creation_result.json")

if __name__ == "__main__":
    main() 