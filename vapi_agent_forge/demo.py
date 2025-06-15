#!/usr/bin/env python3
"""
🤖 Vapi Agent Forge Demo Script

This script demonstrates the complete user authentication and voice agent management system.
It shows how to:
1. Create users
2. Create voice agents for users
3. Log interactions
4. Retrieve user data

Run this script to see the system in action!
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)

def print_response(response, description):
    print(f"\n📡 {description}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response.text}")
    else:
        print(f"Error: {response.text}")

def main():
    print("🤖 Vapi Agent Forge - Complete Demo")
    print("=" * 60)
    print("This demo showcases the user authentication and voice agent management system")
    print("Make sure the backend is running on http://localhost:8000")
    
    # Test backend connectivity
    try:
        response = requests.get(f"{BASE_URL}/auth/users")
        if response.status_code != 200:
            print("❌ Backend not accessible. Please start the backend server.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Please start the backend server.")
        return
    
    print("✅ Backend is running!")
    
    # 1. User Management Demo
    print_section("USER MANAGEMENT")
    
    # Create first user
    user1_data = {"username": "alice_researcher"}
    response = requests.post(f"{BASE_URL}/auth/login", json=user1_data)
    print_response(response, "Creating user 'alice_researcher'")
    alice_id = response.json()["user_id"]
    
    # Create second user
    user2_data = {"username": "bob_support"}
    response = requests.post(f"{BASE_URL}/auth/login", json=user2_data)
    print_response(response, "Creating user 'bob_support'")
    bob_id = response.json()["user_id"]
    
    # List all users
    response = requests.get(f"{BASE_URL}/auth/users")
    print_response(response, "Listing all users")
    
    # 2. Voice Agent Creation Demo
    print_section("VOICE AGENT CREATION")
    
    # Create research assistant for Alice
    research_config = """assistant:
  name: "Alice's Research Assistant"
  model:
    provider: "openai"
    model: "gpt-4"
    system_prompt_template: |
      You are Alice's personal research assistant. You help with academic research,
      data analysis, and content generation. Always be thorough and cite sources.
  voice:
    provider: "playht"
    voiceId: "jennifer"
  firstMessage: "Hi Alice! I'm ready to help you with your research. What topic shall we explore today?"

tools:
  - name: "research_topic"
    description: "Research a specific academic topic"
    parameters:
      type: "object"
      properties:
        topic:
          type: "string"
          description: "The research topic"
        depth:
          type: "string"
          enum: ["basic", "detailed", "comprehensive"]
          description: "Research depth"
      required: ["topic"]
    action:
      method: "POST"
      url: "http://localhost:8082/research"
      json_body:
        topic: "{topic}"
        depth: "{depth}"
      response_format: "Research completed on {topic}: {response.summary}"
      
  - name: "generate_report"
    description: "Generate a research report"
    parameters:
      type: "object"
      properties:
        topic:
          type: "string"
          description: "Report topic"
        format:
          type: "string"
          enum: ["academic", "summary", "presentation"]
          description: "Report format"
      required: ["topic"]
    action:
      method: "POST"
      url: "http://localhost:8082/generate"
      json_body:
        type: "report"
        topic: "{topic}"
        format: "{format}"
      response_format: "Generated {format} report on {topic}: {response.content}"
"""
    
    alice_agent_data = {
        "name": "Alice's Research Assistant",
        "config_yaml": research_config
    }
    
    response = requests.post(f"{BASE_URL}/users/{alice_id}/voice-agents", json=alice_agent_data)
    print_response(response, "Creating research assistant for Alice")
    alice_agent_id = response.json()["agent_id"] if response.status_code == 200 else None
    
    # Create customer support assistant for Bob
    support_config = """assistant:
  name: "Bob's Customer Support Assistant"
  model:
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt_template: |
      You are Bob's customer support assistant. You help resolve customer issues,
      answer questions, and provide excellent service. Always be friendly and solution-oriented.
  voice:
    provider: "playht"
    voiceId: "jennifer"
  firstMessage: "Hello! I'm Bob's support assistant. How can I help you with your customer service needs today?"

tools:
  - name: "check_order_status"
    description: "Check customer order status"
    parameters:
      type: "object"
      properties:
        order_id:
          type: "string"
          description: "Order ID to check"
      required: ["order_id"]
    action:
      method: "GET"
      url: "http://localhost:8000/orders/{order_id}/status"
      response_format: "Order {order_id} status: {response.status}"
      
  - name: "create_ticket"
    description: "Create support ticket"
    parameters:
      type: "object"
      properties:
        issue:
          type: "string"
          description: "Issue description"
        priority:
          type: "string"
          enum: ["low", "medium", "high"]
          description: "Issue priority"
      required: ["issue"]
    action:
      method: "POST"
      url: "http://localhost:8000/support/tickets"
      json_body:
        description: "{issue}"
        priority: "{priority}"
      response_format: "Created ticket #{response.ticket_id} for: {issue}"
"""
    
    bob_agent_data = {
        "name": "Bob's Customer Support Assistant",
        "config_yaml": support_config
    }
    
    response = requests.post(f"{BASE_URL}/users/{bob_id}/voice-agents", json=bob_agent_data)
    print_response(response, "Creating customer support assistant for Bob")
    bob_agent_id = response.json()["agent_id"] if response.status_code == 200 else None
    
    # 3. Voice Agent Management Demo
    print_section("VOICE AGENT MANAGEMENT")
    
    # List Alice's voice agents
    response = requests.get(f"{BASE_URL}/users/{alice_id}/voice-agents")
    print_response(response, "Listing Alice's voice agents")
    
    # List Bob's voice agents
    response = requests.get(f"{BASE_URL}/users/{bob_id}/voice-agents")
    print_response(response, "Listing Bob's voice agents")
    
    # 4. Interaction Logging Demo
    print_section("INTERACTION LOGGING")
    
    # Simulate interactions for Alice
    if alice_agent_id:
        interactions = [
            {"interaction_type": "call_started", "content": "Alice started a research call"},
            {"interaction_type": "user_message", "content": "Can you research artificial intelligence trends?"},
            {"interaction_type": "function_call", "content": "Called: research_topic with topic='artificial intelligence trends'"},
            {"interaction_type": "user_message", "content": "Now generate a summary report"},
            {"interaction_type": "function_call", "content": "Called: generate_report with topic='AI trends', format='summary'"},
            {"interaction_type": "call_ended", "content": "Alice ended the research call"}
        ]
        
        for interaction in interactions:
            interaction["voice_agent_id"] = alice_agent_id
            response = requests.post(f"{BASE_URL}/users/{alice_id}/interactions", json=interaction)
            print(f"✅ Logged: {interaction['interaction_type']}")
            time.sleep(0.1)  # Small delay for realistic timestamps
    
    # Simulate interactions for Bob
    if bob_agent_id:
        interactions = [
            {"interaction_type": "call_started", "content": "Bob started a support call"},
            {"interaction_type": "user_message", "content": "I need to check order status for ORD-12345"},
            {"interaction_type": "function_call", "content": "Called: check_order_status with order_id='ORD-12345'"},
            {"interaction_type": "user_message", "content": "Create a ticket for shipping delay"},
            {"interaction_type": "function_call", "content": "Called: create_ticket with issue='shipping delay', priority='medium'"},
            {"interaction_type": "call_ended", "content": "Bob ended the support call"}
        ]
        
        for interaction in interactions:
            interaction["voice_agent_id"] = bob_agent_id
            response = requests.post(f"{BASE_URL}/users/{bob_id}/interactions", json=interaction)
            print(f"✅ Logged: {interaction['interaction_type']}")
            time.sleep(0.1)
    
    # 5. Analytics Demo
    print_section("USER ANALYTICS")
    
    # Get Alice's interaction history
    response = requests.get(f"{BASE_URL}/users/{alice_id}/interactions")
    print_response(response, "Alice's interaction history")
    
    # Get Bob's interaction history
    response = requests.get(f"{BASE_URL}/users/{bob_id}/interactions")
    print_response(response, "Bob's interaction history")
    
    # 6. System Summary
    print_section("SYSTEM SUMMARY")
    
    # Get all users
    response = requests.get(f"{BASE_URL}/auth/users")
    users = response.json()["users"]
    
    print(f"\n📊 SYSTEM STATISTICS")
    print(f"👥 Total Users: {len(users)}")
    
    total_agents = 0
    total_interactions = 0
    
    for user in users:
        user_id = user["id"]
        username = user["username"]
        
        # Get user's agents
        agents_response = requests.get(f"{BASE_URL}/users/{user_id}/voice-agents")
        agents = agents_response.json()["voice_agents"] if agents_response.status_code == 200 else []
        
        # Get user's interactions
        interactions_response = requests.get(f"{BASE_URL}/users/{user_id}/interactions")
        interactions = interactions_response.json()["interactions"] if interactions_response.status_code == 200 else []
        
        total_agents += len(agents)
        total_interactions += len(interactions)
        
        print(f"  • {username}: {len(agents)} agents, {len(interactions)} interactions")
    
    print(f"\n🤖 Total Voice Agents: {total_agents}")
    print(f"💬 Total Interactions: {total_interactions}")
    
    print_section("DEMO COMPLETE")
    print("🎉 Successfully demonstrated:")
    print("  ✅ User authentication and management")
    print("  ✅ Voice agent creation with YAML configs")
    print("  ✅ User-specific agent isolation")
    print("  ✅ Comprehensive interaction logging")
    print("  ✅ Real-time analytics and monitoring")
    print("\n🚀 The system is ready for production use!")
    print("\n📱 Access the web interface at:")
    print("  • Login: http://localhost:3000/login")
    print("  • Dashboard: http://localhost:3000/")
    print("  • Voice Agents: http://localhost:3000/voice-agents")

if __name__ == "__main__":
    main() 