#!/usr/bin/env python3
import asyncio
import yaml
import json
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set PUBLIC_SERVER_URL
os.environ["PUBLIC_SERVER_URL"] = "https://d6c5-2603-8000-baf0-4690-4c7d-38bd-11e8-5920.ngrok-free.app"

# Import the function we want to test
from main import create_vapi_assistant_from_config

async def test_vapi_creation():
    print("🔍 Testing VAPI assistant creation...")
    
    # Get user's VAPI API key from database
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    cursor.execute("SELECT vapi_api_key FROM users WHERE id = ?", (4,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        print("❌ No VAPI API key found for user 4")
        return
    
    user_vapi_key = result[0]
    print(f"✅ Found VAPI API key (length: {len(user_vapi_key)})")
    
    # Load simple test config
    with open('simple_test.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ Loaded config: {json.dumps(config, indent=2)}")
    
    try:
        # Test the function directly
        result = await create_vapi_assistant_from_config(config, user_vapi_key, 4)
        print(f"✅ Success! Assistant created: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vapi_creation()) 