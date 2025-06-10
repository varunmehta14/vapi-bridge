#!/usr/bin/env python3
"""Debug script to check Vapi API request payload"""

import json
import yaml

def debug_vapi_payload():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    user_id = 'demo_user_123'
    assistant_config = config['assistant']
    
    # Build the assistant payload like the orchestrator does
    vapi_assistant = {
        'name': f"{assistant_config['name']} - {user_id}",
        'model': assistant_config['model'].copy(),
        'voice': assistant_config['voice'],
        'firstMessage': assistant_config['firstMessage']
    }
    
    # Handle system prompt
    if 'system_prompt_template' in assistant_config['model']:
        system_prompt = assistant_config['model']['system_prompt_template'].format(user_id=user_id)
        vapi_assistant['model']['systemPrompt'] = system_prompt
        del vapi_assistant['model']['system_prompt_template']
    
    # Convert tools
    vapi_tools = []
    for tool in config['tools']:
        vapi_tool = {
            'type': 'function',
            'function': {
                'name': tool['name'],
                'description': tool['description'],
                'parameters': tool['parameters']
            }
        }
        vapi_tools.append(vapi_tool)
    
    vapi_assistant['tools'] = vapi_tools
    vapi_assistant['server'] = {
        'url': 'https://6dcc-2603-8000-baf0-4690-4103-a158-bc73-6888.ngrok-free.app/webhook/tool-call'
    }
    
    print('📋 Request payload that would be sent to Vapi:')
    print(json.dumps(vapi_assistant, indent=2))
    print('\n🔍 Checking for common issues...')
    
    # Check for common issues
    if 'systemPrompt' not in vapi_assistant['model']:
        print('⚠️  Missing systemPrompt in model')
    
    if not vapi_assistant['tools']:
        print('⚠️  No tools defined')
    
    for i, tool in enumerate(vapi_assistant['tools']):
        if 'type' not in tool:
            print(f'⚠️  Tool {i}: Missing type')
        if 'function' not in tool:
            print(f'⚠️  Tool {i}: Missing function')
        elif 'parameters' not in tool['function']:
            print(f'⚠️  Tool {i}: Missing parameters in function')

if __name__ == "__main__":
    debug_vapi_payload() 