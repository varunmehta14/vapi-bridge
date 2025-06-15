from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import yaml
import httpx
import os
import re
import uvicorn
import json
from dotenv import load_dotenv
import time
import sqlite3
from datetime import datetime
import uuid

# Import the new service registry
from service_registry import ServiceRegistry, get_service_registry, resolve_service_url

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Vapi Agent Forge",
    description="Dynamic Vapi system that interfaces with the Tesseract Workflow Engine",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Environment variable for public server URL (for ngrok)
PUBLIC_SERVER_URL = os.getenv("PUBLIC_SERVER_URL", "http://localhost:8000")
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY", "")

# Initialize SQLite database for users and voice agents
def init_database():
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    # Users table with VAPI API key support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            vapi_api_key TEXT,
            vapi_public_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add vapi_api_key column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN vapi_api_key TEXT')
        cursor.execute('ALTER TABLE users ADD COLUMN vapi_public_key TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Voice agents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            vapi_assistant_id TEXT,
            config_yaml TEXT,
            agent_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Interactions log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            voice_agent_id INTEGER,
            interaction_type TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (voice_agent_id) REFERENCES voice_agents (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Pydantic models for users and voice agents
class User(BaseModel):
    username: str
    email: Optional[str] = None
    vapi_api_key: Optional[str] = None
    vapi_public_key: Optional[str] = None

class VoiceAgent(BaseModel):
    name: str
    config_yaml: str
    agent_type: Optional[str] = "custom"

class UserLogin(BaseModel):
    username: str
    vapi_api_key: Optional[str] = None
    vapi_public_key: Optional[str] = None

class UserSignup(BaseModel):
    username: str
    email: Optional[str] = None
    vapi_api_key: str
    vapi_public_key: Optional[str] = None

# User management endpoints
@app.post("/auth/signup")
async def signup_user(user_data: UserSignup):
    """Create a new user with VAPI API key"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user with VAPI API key
        cursor.execute('''
            INSERT INTO users (username, email, vapi_api_key, vapi_public_key) 
            VALUES (?, ?, ?, ?)
        ''', (user_data.username, user_data.email, user_data.vapi_api_key, user_data.vapi_public_key))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        return {
            "user_id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "vapi_configured": True,
            "message": "Account created successfully",
            "status": "success"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    finally:
        conn.close()

@app.post("/auth/login")
async def login_user(user_data: UserLogin):
    """Login user and optionally update VAPI API key"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, username, email, vapi_api_key, vapi_public_key FROM users WHERE username = ?", (user_data.username,))
    user = cursor.fetchone()
    
    if not user:
        # Create new user if doesn't exist (backward compatibility)
        cursor.execute("INSERT INTO users (username, vapi_api_key, vapi_public_key) VALUES (?, ?, ?)", 
                      (user_data.username, user_data.vapi_api_key, user_data.vapi_public_key))
        user_id = cursor.lastrowid
        conn.commit()
        user = (user_id, user_data.username, None, user_data.vapi_api_key, user_data.vapi_public_key)
    else:
        # Update VAPI keys if provided
        if user_data.vapi_api_key:
            cursor.execute('''
                UPDATE users SET vapi_api_key = ?, vapi_public_key = ? WHERE id = ?
            ''', (user_data.vapi_api_key, user_data.vapi_public_key, user[0]))
            conn.commit()
    
    conn.close()
    
    return {
        "user_id": user[0],
        "username": user[1],
        "email": user[2] if len(user) > 2 else None,
        "vapi_configured": bool(user[3] if len(user) > 3 else user_data.vapi_api_key),
        "message": "Login successful",
        "status": "success"
    }

@app.get("/auth/users")
async def list_users():
    """List all users for simple selection"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, created_at, CASE WHEN vapi_api_key IS NOT NULL THEN 1 ELSE 0 END as vapi_configured FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    return {
        "users": [
            {
                "id": user[0], 
                "username": user[1], 
                "email": user[2],
                "created_at": user[3],
                "vapi_configured": bool(user[4])
            } for user in users
        ],
        "status": "success"
    }

@app.get("/users/{user_id}/vapi-config")
async def get_user_vapi_config(user_id: int):
    """Get user's VAPI configuration status"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT vapi_api_key, vapi_public_key FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "vapi_configured": bool(user[0]),
        "has_public_key": bool(user[1]),
        "status": "success"
    }

@app.get("/users/{user_id}/vapi-public-key")
async def get_user_vapi_public_key(user_id: int):
    """Get user's VAPI public key for web SDK"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT vapi_public_key FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user[0]:
        raise HTTPException(status_code=400, detail="User has not configured VAPI public key")
    
    return {
        "public_key": user[0],
        "status": "success"
    }

@app.post("/users/{user_id}/vapi-config")
async def update_user_vapi_config(user_id: int, vapi_data: dict):
    """Update user's VAPI API keys"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users SET vapi_api_key = ?, vapi_public_key = ? WHERE id = ?
        ''', (vapi_data.get('vapi_api_key'), vapi_data.get('vapi_public_key'), user_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn.commit()
        
        return {
            "message": "VAPI configuration updated successfully",
            "status": "success"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update VAPI config: {str(e)}")
    finally:
        conn.close()

# Helper function to get user's VAPI API key
async def get_user_vapi_key(user_id: int) -> Optional[str]:
    """Get user's VAPI API key"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT vapi_api_key FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

# User-specific service configuration endpoints
class UserServiceConfig(BaseModel):
    service_name: str
    service_url: str
    health_path: Optional[str] = "/health"
    timeout: Optional[int] = 10
    required: Optional[bool] = True

@app.post("/users/{user_id}/services")
async def configure_user_service(user_id: int, service_config: UserServiceConfig):
    """Configure a service URL for a specific user"""
    try:
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        # Create user_services table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_name TEXT NOT NULL,
                service_url TEXT NOT NULL,
                health_path TEXT DEFAULT '/health',
                timeout INTEGER DEFAULT 10,
                required BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, service_name)
            )
        ''')
        
        # Insert or update service configuration
        cursor.execute('''
            INSERT OR REPLACE INTO user_services 
            (user_id, service_name, service_url, health_path, timeout, required, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, service_config.service_name, service_config.service_url, 
              service_config.health_path, service_config.timeout, service_config.required))
        
        conn.commit()
        conn.close()
        
        # Log interaction
        await log_interaction(user_id, None, "service_configured", 
                            f"Configured service: {service_config.service_name} -> {service_config.service_url}")
        
        return {
            "message": f"Service '{service_config.service_name}' configured successfully",
            "service": {
                "name": service_config.service_name,
                "url": service_config.service_url,
                "health_path": service_config.health_path,
                "timeout": service_config.timeout,
                "required": service_config.required
            },
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure service: {str(e)}")

@app.get("/users/{user_id}/services")
async def get_user_services(user_id: int):
    """Get all configured services for a user"""
    try:
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_name TEXT NOT NULL,
                service_url TEXT NOT NULL,
                health_path TEXT DEFAULT '/health',
                timeout INTEGER DEFAULT 10,
                required BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, service_name)
            )
        ''')
        
        cursor.execute('''
            SELECT service_name, service_url, health_path, timeout, required, created_at, updated_at
            FROM user_services WHERE user_id = ? ORDER BY service_name
        ''', (user_id,))
        
        services = cursor.fetchall()
        conn.close()
        
        return {
            "services": [
                {
                    "name": service[0],
                    "url": service[1],
                    "health_path": service[2],
                    "timeout": service[3],
                    "required": bool(service[4]),
                    "created_at": service[5],
                    "updated_at": service[6]
                }
                for service in services
            ],
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user services: {str(e)}")

@app.delete("/users/{user_id}/services/{service_name}")
async def delete_user_service(user_id: int, service_name: str):
    """Delete a configured service for a user"""
    try:
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_services WHERE user_id = ? AND service_name = ?", 
                      (user_id, service_name))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service configuration not found")
        
        conn.commit()
        conn.close()
        
        # Log interaction
        await log_interaction(user_id, None, "service_deleted", f"Deleted service: {service_name}")
        
        return {
            "message": f"Service '{service_name}' configuration deleted successfully",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete service: {str(e)}")

@app.post("/users/{user_id}/services/{service_name}/test")
async def test_user_service(user_id: int, service_name: str):
    """Test a user's configured service"""
    try:
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT service_url, health_path, timeout FROM user_services 
            WHERE user_id = ? AND service_name = ?
        ''', (user_id, service_name))
        
        service = cursor.fetchone()
        conn.close()
        
        if not service:
            raise HTTPException(status_code=404, detail="Service configuration not found")
        
        service_url, health_path, timeout = service
        health_url = f"{service_url.rstrip('/')}{health_path}"
        
        # Test the service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(health_url, timeout=timeout)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return {
                            "service_name": service_name,
                            "status": "healthy",
                            "url": service_url,
                            "health_url": health_url,
                            "response": data,
                            "message": "Service is responding correctly"
                        }
                    except:
                        return {
                            "service_name": service_name,
                            "status": "healthy",
                            "url": service_url,
                            "health_url": health_url,
                            "response": response.text,
                            "message": "Service is responding correctly"
                        }
                else:
                    return {
                        "service_name": service_name,
                        "status": "unhealthy",
                        "url": service_url,
                        "health_url": health_url,
                        "error": f"HTTP {response.status_code}",
                        "message": "Service returned error status"
                    }
                    
            except httpx.TimeoutException:
                return {
                    "service_name": service_name,
                    "status": "timeout",
                    "url": service_url,
                    "health_url": health_url,
                    "error": "Connection timeout",
                    "message": f"Service did not respond within {timeout} seconds"
                }
            except Exception as e:
                return {
                    "service_name": service_name,
                    "status": "error",
                    "url": service_url,
                    "health_url": health_url,
                    "error": str(e),
                    "message": "Failed to connect to service"
                }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test service: {str(e)}")

# User-specific tool executor that uses their configured services
class UserToolExecutor:
    """Tool executor that uses user-specific service configurations"""
    
    def __init__(self, user_id: int, config: Dict[str, Any]):
        self.user_id = user_id
        self.config = config
        self.tools = {tool["name"]: tool for tool in config["tools"]}
        self.user_services = {}
        
    async def load_user_services(self):
        """Load user's configured services"""
        try:
            conn = sqlite3.connect('vapi_forge.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT service_name, service_url FROM user_services WHERE user_id = ?
            ''', (self.user_id,))
            
            services = cursor.fetchall()
            conn.close()
            
            self.user_services = {service[0]: service[1] for service in services}
            
        except Exception as e:
            print(f"Failed to load user services: {e}")
            self.user_services = {}
    
    def resolve_user_url(self, url_template: str) -> str:
        """Resolve URL using user's configured services"""
        # Handle direct HTTP/HTTPS URLs - pass them through unchanged
        if url_template.startswith(('http://', 'https://')):
            print(f"🔗 Using direct URL: {url_template}")
            return url_template
            
        # Handle service:// URLs with user's services
        if url_template.startswith('service://'):
            parts = url_template[10:].split('/', 1)  # Remove 'service://'
            service_name = parts[0]
            endpoint = f"/{parts[1]}" if len(parts) > 1 else ""
            
            if service_name in self.user_services:
                base_url = self.user_services[service_name].rstrip('/')
                resolved_url = f"{base_url}{endpoint}"
                print(f"🔗 Resolved service URL: {url_template} -> {resolved_url}")
                return resolved_url
            else:
                # Fallback to default service registry
                registry = get_service_registry()
                resolved_url = registry.resolve_tool_url({"url": url_template})
                print(f"🔗 Registry resolved URL: {url_template} -> {resolved_url}")
                return resolved_url
        
        # Handle ${VAR} substitution - could be enhanced to use user-specific env vars
        if '${' in url_template:
            import re
            def replace_var(match):
                var_name = match.group(1)
                # Check if user has this service configured
                if var_name.endswith('_SERVICE_URL'):
                    service_name = var_name.replace('_SERVICE_URL', '').lower()
                    if service_name in self.user_services:
                        return self.user_services[service_name]
                # Fallback to environment variable
                return os.getenv(var_name, match.group(0))
            
            resolved_url = re.sub(r'\$\{([^}]+)\}', replace_var, url_template)
            print(f"🔗 Variable resolved URL: {url_template} -> {resolved_url}")
            return resolved_url
        
        print(f"🔗 URL passed through unchanged: {url_template}")
        return url_template
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with user-specific service resolution"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        print(f"🔧 Executing tool: {tool_name} for user {self.user_id}")
        print(f"🔧 Parameters: {json.dumps(parameters, indent=2)}")

        # Load user services if not already loaded
        if not self.user_services:
            await self.load_user_services()
            print(f"🔧 Loaded user services: {list(self.user_services.keys())}")

        tool_config = self.tools[tool_name]
        action_config = tool_config["action"]

        # Resolve URL using user's services
        method = action_config["method"]
        url_template = action_config["url"]
        resolved_url = self.resolve_user_url(url_template)

        # Replace URL parameters
        url = self._replace_placeholders(resolved_url, parameters)
        print(f"🌐 Final URL: {url}")

        # Prepare request body
        json_body = None
        if "json_body" in action_config:
            json_body = self._replace_placeholders_in_dict(action_config["json_body"], parameters)
            print(f"📤 Request body: {json.dumps(json_body, indent=2)}")

        # Make the API call
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                print(f"🚀 Making {method.upper()} request to: {url}")
                
                if method.upper() == "POST":
                    response = await client.post(url, json=json_body)
                elif method.upper() == "GET":
                    response = await client.get(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                print(f"📥 Response status: {response.status_code}")
                print(f"📥 Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                response_data = response.json()
                print(f"📥 Response data: {json.dumps(response_data, indent=2)}")

                # Format the response according to tool configuration
                formatted_response = self._format_response(tool_config, response_data, parameters)
                print(f"✅ Formatted response: {formatted_response}")
                return formatted_response

            except httpx.HTTPError as e:
                error_msg = f"API call failed: {str(e)}"
                print(f"❌ HTTP Error: {error_msg}")
                if hasattr(e, 'response') and e.response:
                    print(f"❌ Response status: {e.response.status_code}")
                    print(f"❌ Response text: {e.response.text}")
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                print(f"❌ Execution Error: {error_msg}")
                raise Exception(error_msg)
    
    def _replace_placeholders(self, template: str, parameters: Dict[str, Any]) -> str:
        """Replace {parameter} placeholders in strings"""
        for key, value in parameters.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
    
    def _replace_placeholders_in_dict(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively replace placeholders in dictionary structures"""
        if isinstance(data, dict):
            return {k: self._replace_placeholders_in_dict(v, parameters) for k, v in data.items()}
        elif isinstance(data, str):
            return self._replace_placeholders(data, parameters)
        else:
            return data
    
    def _format_response(self, tool_config: Dict[str, Any], response_data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Format the response according to tool configuration"""
        action_config = tool_config["action"]
        
        # Check if there's a response_template
        if "response_template" in action_config:
            template = action_config["response_template"]
            # Replace placeholders with response data
            for key, value in response_data.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        
        # Check if there's a response_path for extracting specific data
        elif "response_path" in action_config:
            path = action_config["response_path"]
            if path in response_data:
                return str(response_data[path])
            else:
                raise ValueError(f"Response path '{path}' not found in API response")
        
        # Default: return the entire response as JSON string
        else:
            return json.dumps(response_data, indent=2)

# Voice agent management endpoints
@app.post("/users/{user_id}/voice-agents")
async def create_voice_agent(user_id: int, agent_data: VoiceAgent):
    """Create a new voice agent for a user using their VAPI API key"""
    try:
        # Get user's VAPI API key
        user_vapi_key = await get_user_vapi_key(user_id)
        if not user_vapi_key:
            raise HTTPException(status_code=400, detail="User has not configured VAPI API key. Please add your VAPI API key in settings.")
        
        # Parse YAML to detect agent type
        config = yaml.safe_load(agent_data.config_yaml)
        agent_type = detect_agent_type(config)
        
        # Create Vapi assistant using user's API key
        vapi_assistant = await create_vapi_assistant_from_config(config, user_vapi_key, user_id)
        
        # Store in database
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO voice_agents (user_id, name, vapi_assistant_id, config_yaml, agent_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, agent_data.name, vapi_assistant["id"], agent_data.config_yaml, agent_type))
        
        agent_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log interaction
        await log_interaction(user_id, agent_id, "agent_created", f"Created voice agent: {agent_data.name}")
        
        return {
            "agent_id": agent_id,
            "vapi_assistant_id": vapi_assistant["id"],
            "name": agent_data.name,
            "agent_type": agent_type,
            "message": "Voice agent created successfully",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create voice agent: {str(e)}")

@app.get("/users/{user_id}/voice-agents")
async def get_user_voice_agents(user_id: int):
    """Get all voice agents for a user"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, vapi_assistant_id, agent_type, created_at, updated_at
        FROM voice_agents WHERE user_id = ? ORDER BY updated_at DESC
    ''', (user_id,))
    
    agents = cursor.fetchall()
    conn.close()
    
    return {
        "voice_agents": [
            {
                "id": agent[0],
                "name": agent[1],
                "vapi_assistant_id": agent[2],
                "agent_type": agent[3],
                "created_at": agent[4],
                "updated_at": agent[5]
            }
            for agent in agents
        ],
        "status": "success"
    }

@app.delete("/users/{user_id}/voice-agents/{agent_id}")
async def delete_voice_agent(user_id: int, agent_id: int):
    """Delete a voice agent"""
    try:
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        # Get agent details
        cursor.execute("SELECT vapi_assistant_id, name FROM voice_agents WHERE id = ? AND user_id = ?", (agent_id, user_id))
        agent = cursor.fetchone()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Voice agent not found")
        
        # Delete from Vapi (optional - you might want to keep for reuse)
        # await delete_vapi_assistant(agent[0])
        
        # Delete from database
        cursor.execute("DELETE FROM voice_agents WHERE id = ? AND user_id = ?", (agent_id, user_id))
        conn.commit()
        conn.close()
        
        # Log interaction
        await log_interaction(user_id, agent_id, "agent_deleted", f"Deleted voice agent: {agent[1]}")
        
        return {
            "message": f"Voice agent '{agent[1]}' deleted successfully",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete voice agent: {str(e)}")

# Interaction logging
async def log_interaction(user_id: int, voice_agent_id: int, interaction_type: str, content: str):
    """Log user interactions"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO interactions (user_id, voice_agent_id, interaction_type, content)
        VALUES (?, ?, ?, ?)
    ''', (user_id, voice_agent_id, interaction_type, content))
    
    conn.commit()
    conn.close()

@app.get("/users/{user_id}/interactions")
async def get_user_interactions(user_id: int, limit: int = 50):
    """Get user interaction history"""
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT i.interaction_type, i.content, i.timestamp, va.name as agent_name
        FROM interactions i
        LEFT JOIN voice_agents va ON i.voice_agent_id = va.id
        WHERE i.user_id = ?
        ORDER BY i.timestamp DESC
        LIMIT ?
    ''', (user_id, limit))
    
    interactions = cursor.fetchall()
    conn.close()
    
    return {
        "interactions": [
            {
                "type": interaction[0],
                "content": interaction[1],
                "timestamp": interaction[2],
                "agent_name": interaction[3]
            }
            for interaction in interactions
        ],
        "status": "success"
    }

# Helper functions
def detect_agent_type(config: dict) -> str:
    """Detect agent type from configuration"""
    tools = config.get("tools", [])
    tool_names = [tool.get("name", "").lower() for tool in tools]
    
    if any("research" in name or "content" in name for name in tool_names):
        return "research"
    elif any("financial" in name or "workflow" in name for name in tool_names):
        return "workflow"
    else:
        return "custom"

async def create_vapi_assistant_from_config(config: dict, user_vapi_key: str, user_id: int) -> dict:
    """Create Vapi assistant from configuration using user's API key with dynamic tool creation"""
    
    print(f"🔍 Creating VAPI assistant for user {user_id}")
    print(f"🔍 VAPI key length: {len(user_vapi_key) if user_vapi_key else 0}")
    print(f"🔍 PUBLIC_SERVER_URL: {PUBLIC_SERVER_URL}")
    
    # Handle both old and new YAML formats
    if "assistant" in config:
        # New format with assistant key
        assistant_config = config["assistant"]
        tools_config = config.get("tools", [])
    else:
        # Direct format (backward compatibility)
        assistant_config = config
        tools_config = config.get("tools", [])
    
    print(f"🔍 Assistant config: {assistant_config}")
    print(f"🔍 Tools count: {len(tools_config)}")
    
    # First, create tools separately
    tool_ids = []
    for tool in tools_config:
        tool_data = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            },
            "server": {
                "url": f"{PUBLIC_SERVER_URL}/webhook/tool-call"
            }
        }
        
        # Create the tool via API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.vapi.ai/tool",
                    headers={
                        "Authorization": f"Bearer {user_vapi_key}",
                        "Content-Type": "application/json"
                    },
                    json=tool_data,
                    timeout=30.0
                )
                response.raise_for_status()
                tool_result = response.json()
                tool_ids.append(tool_result["id"])
                print(f"✅ Created tool: {tool['name']} (ID: {tool_result['id']})")
                
            except httpx.HTTPError as e:
                print(f"⚠️  Failed to create tool {tool['name']}: {str(e)}")
                continue
    
    print(f"✅ Created {len(tool_ids)} tools successfully")
    
    # Get system prompt from messages array or fallback to system_prompt_template
    system_prompt = "You are a helpful AI assistant."  # Default fallback
    
    if "messages" in assistant_config["model"]:
        # Extract from messages array (new format)
        for message in assistant_config["model"]["messages"]:
            if message.get("role") == "system":
                system_prompt = message.get("content", system_prompt)
                break
    elif "system_prompt_template" in assistant_config["model"]:
        # Fallback to old format
        system_prompt = assistant_config["model"]["system_prompt_template"]
    
    # Replace {user_id} placeholder
    system_prompt = system_prompt.replace("{user_id}", str(user_id))
    
    # Prepare the assistant configuration with shorter name
    assistant_name = f"Tesseract AI - {user_id}"
    vapi_assistant = {
        "name": assistant_name,
        "model": {
            "provider": assistant_config["model"]["provider"],
            "model": assistant_config["model"]["model"],
            "messages": [{
                "role": "system",
                "content": system_prompt
            }]
        },
        "voice": assistant_config["voice"],
        "firstMessage": assistant_config["firstMessage"]
    }
    
    # Add tool IDs to the model (not inline tools)
    if tool_ids:
        vapi_assistant["model"]["toolIds"] = tool_ids
    
    print(f"🔍 VAPI Assistant Config:")
    print(f"   Name: {vapi_assistant['name']}")
    print(f"   Model: {vapi_assistant['model']['model']}")
    print(f"   Tool IDs: {tool_ids}")
    print(f"   Webhook: {PUBLIC_SERVER_URL}/webhook/tool-call")
    
    # Create via Vapi API
    async with httpx.AsyncClient() as client:
        try:
            print(f"🚀 Creating VAPI assistant...")
            response = await client.post(
                "https://api.vapi.ai/assistant",
                headers={
                    "Authorization": f"Bearer {user_vapi_key}",
                    "Content-Type": "application/json"
                },
                json=vapi_assistant,
                timeout=30.0
            )
            
            print(f"📡 VAPI API Response: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                
                print(f"✅ SUCCESS! Assistant created:")
                print(f"   Assistant ID: {result['id']}")
                print(f"   Name: {result['name']}")
                print(f"   Tool IDs referenced: {len(tool_ids)}")
                
                return result
            else:
                error_detail = f"Vapi API error: {response.status_code} - {response.text}"
                print(f"❌ VAPI API error: {error_detail}")
                raise HTTPException(status_code=400, detail=error_detail)
            
        except Exception as e:
            print(f"❌ Exception in VAPI API call: {str(e)}")
            raise e

# Update existing webhook to forward to LangGraph service
@app.post("/webhook/tool-call")
async def handle_tool_call(request: Request):
    """
    Handle Vapi tool calls and forward them to the LangGraph service for processing
    
    Args:
        request: Raw FastAPI request from Vapi
        
    Returns:
        Response from LangGraph service
    """
    print(f"\n{'='*80}")
    print(f"🎯 WEBHOOK TOOL CALL RECEIVED at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Request method: {request.method}")
    print(f"🎯 Request URL: {request.url}")
    print(f"{'='*80}")
    
    try:
        # Get the raw JSON data from Vapi
        raw_data = await request.json()
        print(f"🔍 Raw webhook data from Vapi: {json.dumps(raw_data, indent=2)}")
        
        # Extract user information for logging
        user_id = 1  # Default user for demo
        if "call" in raw_data and "customer" in raw_data["call"]:
            customer = raw_data["call"]["customer"]
            if "number" in customer:
                user_id = 1  # You could map phone numbers to user IDs here
        
        print(f"👤 User ID: {user_id}")
        
        # Get LangGraph service URL from user services or use default
        langgraph_url = None
        try:
            # Try to get user's configured LangGraph service
            with sqlite3.connect('vapi_forge.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT service_url FROM user_services 
                    WHERE user_id = ? AND service_name = 'langgraph'
                """, (user_id,))
                result = cursor.fetchone()
                if result:
                    langgraph_url = result[0]
        except Exception as e:
            print(f"⚠️ Could not get user's LangGraph service: {e}")
        
        # Default to localhost if no service configured
        if not langgraph_url:
            langgraph_url = "http://localhost:8082"  # Default LangGraph service (port 8082)
        
        # Ensure URL has no trailing slash
        langgraph_url = langgraph_url.rstrip('/')
        
        print(f"🔄 Forwarding to LangGraph service: {langgraph_url}/vapi-webhook")
        
        # Forward the request to LangGraph service
        async with httpx.AsyncClient() as client:
            try:
                # Forward the exact webhook data to LangGraph
                response = await client.post(
                    f"{langgraph_url}/vapi-webhook",
                    json={
                        "message": raw_data.get("message", raw_data),
                        "call": raw_data.get("call", {})
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ LangGraph response: {result}")
                    
                    # Log successful interaction
                    await log_interaction(user_id, None, "tool_forwarded", "Successfully forwarded to LangGraph")
                    
                    return result
                else:
                    print(f"❌ LangGraph service error: {response.status_code}")
                    print(f"Response: {response.text}")
                    
                    # Fallback to error response
                    return {
                        "result": f"I'm having trouble processing your request. LangGraph service returned status {response.status_code}."
                    }
                    
            except httpx.ConnectError:
                print(f"❌ Cannot connect to LangGraph service at {langgraph_url}")
                return {
                    "result": "I'm currently unavailable. The LangGraph service is not reachable. Please try again later."
                }
            except httpx.TimeoutException:
                print(f"❌ Timeout connecting to LangGraph service")
                return {
                    "result": "I'm taking longer than usual to respond. Please try your request again."
                }
            except Exception as e:
                print(f"❌ Error forwarding to LangGraph: {e}")
                return {
                    "result": f"I encountered an error while processing your request: {str(e)}"
                }
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {"result": f"Error: Invalid request format - {str(e)}"}
    except Exception as e:
        print(f"❌ Unexpected error in webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"result": f"Error: {str(e)}"}

# Add a catch-all webhook endpoint to see if Vapi calls different URLs
@app.post("/webhook/{path:path}")
async def catch_all_webhook(request: Request, path: str):
    """Catch any webhook calls that might not be going to /webhook/tool-call"""
    try:
        raw_data = await request.json()
        print(f"🔍 CATCH-ALL WEBHOOK: /{path}")
        print(f"🔍 Data: {json.dumps(raw_data, indent=2)}")
        return {"result": "Caught by catch-all"}
    except:
        print(f"🔍 CATCH-ALL WEBHOOK: /{path} (no JSON data)")
        return {"result": "Caught by catch-all"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests to help debug webhook issues"""
    if request.url.path.startswith("/webhook") or request.url.path.startswith("/api"):
        print(f"🌐 INCOMING REQUEST: {request.method} {request.url}")
        print(f"🌐 Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    return response

@app.get("/assistant-config")
async def get_assistant_config():
    """
    Get the assistant configuration for creating Vapi assistants
    This endpoint provides the configuration that can be used to programmatically create Vapi assistants
    """
    try:
        # Prepare the assistant configuration with proper server URLs
        assistant_config = config["assistant"].copy()
        
        # Update tool URLs to use the public server URL
        tools = []
        for tool in config["tools"]:
            tool_copy = tool.copy()
            # Update the server URL in tool configurations to use the public URL
            if "action" in tool_copy and "url" in tool_copy["action"]:
                # Replace localhost with the public URL for webhook endpoints
                url = tool_copy["action"]["url"]
                if "localhost" in url:
                    # This is for the Tesseract engine, keep as localhost since it's internal
                    pass
                else:
                    # This would be for any webhook URLs that need to be public
                    tool_copy["action"]["url"] = url.replace("http://localhost:8000", PUBLIC_SERVER_URL)
            tools.append(tool_copy)
        
        assistant_config["tools"] = tools
        
        # Add server configuration for tool calls
        assistant_config["server"] = {
            "url": f"{PUBLIC_SERVER_URL}/webhook/tool-call"
        }
        
        return assistant_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load configuration: {str(e)}")

@app.post("/test-tool/{tool_name}")
async def test_tool(tool_name: str, parameters: Dict[str, Any]):
    """
    Test endpoint for debugging tool execution
    
    Args:
        tool_name: Name of the tool to test
        parameters: Parameters to pass to the tool
        
    Returns:
        Tool execution result
    """
    try:
        result = await tool_executor.execute_tool(tool_name, parameters)
        return {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        return {
            "tool_name": tool_name,
            "parameters": parameters,
            "error": str(e),
            "status": "error"
        }

@app.get("/tools")
async def list_tools():
    """List all available tools"""
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in config["tools"]
        ]
    }

# =================== NEW CONFIGURATION MANAGEMENT ENDPOINTS ===================

@app.get("/config")
async def get_config():
    """Get the current YAML configuration"""
    try:
        return {
            "config": config,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load configuration: {str(e)}")

@app.post("/config")
async def update_config(new_config: Dict[str, Any]):
    """Update the YAML configuration"""
    try:
        # Validate the configuration structure
        required_keys = ["assistant", "tools"]
        for key in required_keys:
            if key not in new_config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        # Validate assistant structure
        assistant = new_config["assistant"]
        required_assistant_keys = ["name", "model", "voice", "firstMessage"]
        for key in required_assistant_keys:
            if key not in assistant:
                raise ValueError(f"Missing required assistant key: {key}")
        
        # Validate tools structure
        if not isinstance(new_config["tools"], list):
            raise ValueError("Tools must be a list")
        
        for i, tool in enumerate(new_config["tools"]):
            required_tool_keys = ["name", "description", "parameters", "action"]
            for key in required_tool_keys:
                if key not in tool:
                    raise ValueError(f"Missing required key '{key}' in tool {i}")
        
        # Save the configuration
        save_config(new_config)
        
        # Reload the tool executor
        reload_tool_executor()
        
        return {
            "message": "Configuration updated successfully",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration validation failed: {str(e)}")

@app.get("/config/yaml")
async def get_config_yaml():
    """Get the current configuration as YAML string"""
    try:
        with open("config.yaml", "r") as file:
            yaml_content = file.read()
        return {
            "yaml": yaml_content,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read YAML file: {str(e)}")

@app.post("/config/yaml")
async def update_config_yaml(yaml_data: Dict[str, str]):
    """Update configuration from YAML string"""
    try:
        yaml_content = yaml_data.get("yaml", "")
        if not yaml_content:
            raise ValueError("No YAML content provided")
        
        # Parse YAML to validate syntax
        try:
            parsed_config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {str(e)}")
        
        # Validate structure (reuse validation from update_config)
        required_keys = ["assistant", "tools"]
        for key in required_keys:
            if key not in parsed_config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        # Save the YAML file
        with open("config.yaml", "w") as file:
            file.write(yaml_content)
        
        # Reload the tool executor
        reload_tool_executor()
        
        return {
            "message": "Configuration updated from YAML successfully",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"YAML update failed: {str(e)}")

@app.post("/config/validate")
async def validate_config_yaml(yaml_data: Dict[str, str]):
    """Validate YAML configuration without saving it"""
    try:
        yaml_content = yaml_data.get("yaml", "")
        if not yaml_content:
            raise ValueError("No YAML content provided")
        
        # Parse YAML to validate syntax
        try:
            parsed_config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return {
                "success": False,
                "message": "Invalid YAML syntax",
                "error": str(e),
                "suggestions": [
                    "Check for proper indentation (use spaces, not tabs)",
                    "Ensure all quotes are properly closed",
                    "Verify colons are followed by spaces",
                    "Check for special characters that need escaping"
                ]
            }
        
        if not parsed_config or not isinstance(parsed_config, dict):
            return {
                "success": False,
                "message": "Invalid configuration structure",
                "error": "Configuration must be a valid YAML object"
            }
        
        # Extract configuration information
        config_info = {}
        validation_results = []
        warnings = []
        
        # Check for assistant section
        if "assistant" in parsed_config:
            assistant = parsed_config["assistant"]
            config_info["name"] = assistant.get("name", "Unnamed Assistant")
            config_info["hasSystemPrompt"] = bool(
                assistant.get("system_prompt_template") or 
                (isinstance(assistant.get("model"), dict) and assistant["model"].get("system_prompt_template"))
            )
            config_info["hasFirstMessage"] = bool(assistant.get("firstMessage"))
            config_info["hasVoice"] = bool(assistant.get("voice"))
            config_info["modelProvider"] = "unknown"
            config_info["voiceProvider"] = "unknown"
            
            # Extract model provider
            if isinstance(assistant.get("model"), dict):
                config_info["modelProvider"] = assistant["model"].get("provider", "unknown")
            elif isinstance(assistant.get("model"), str):
                config_info["modelProvider"] = assistant["model"]
            
            # Extract voice provider
            if isinstance(assistant.get("voice"), dict):
                config_info["voiceProvider"] = assistant["voice"].get("provider", "unknown")
            
            validation_results.append("✅ Assistant section found")
        else:
            warnings.append("⚠️ No assistant section found")
        
        # Check for tools
        tools = parsed_config.get("tools", [])
        if isinstance(tools, list):
            config_info["toolCount"] = len(tools)
            if len(tools) > 0:
                validation_results.append(f"✅ Found {len(tools)} tools configured")
                
                # Analyze tool types
                tool_types = []
                for tool in tools:
                    if isinstance(tool, dict) and "name" in tool:
                        tool_name = tool["name"]
                        if "research" in tool_name.lower() or "generate_content" in tool_name.lower():
                            tool_types.append("research")
                        elif "workflow" in tool_name.lower() or "financial" in tool_name.lower():
                            tool_types.append("workflow")
                        else:
                            tool_types.append("custom")
                
                if "research" in tool_types:
                    config_info["agentType"] = "research"
                    config_info["description"] = "AI-powered research and content generation assistant"
                elif "workflow" in tool_types:
                    config_info["agentType"] = "workflow"
                    config_info["description"] = "Workflow automation and business process assistant"
                else:
                    config_info["agentType"] = "custom"
                    config_info["description"] = f"Custom assistant with {len(tools)} specialized tools"
            else:
                warnings.append("⚠️ No tools configured - assistant will have limited functionality")
                config_info["agentType"] = "unknown"
                config_info["description"] = "Basic assistant without specialized tools"
        else:
            warnings.append("⚠️ Tools section is not a valid list")
            config_info["toolCount"] = 0
        
        # Generate suggestions
        suggestions = []
        if not config_info.get("hasSystemPrompt"):
            suggestions.append("Add a system_prompt_template to define the assistant's behavior")
        if not config_info.get("hasFirstMessage"):
            suggestions.append("Add a firstMessage to greet users when they start a conversation")
        if not config_info.get("hasVoice"):
            suggestions.append("Configure voice settings for better user experience")
        if config_info.get("toolCount", 0) == 0:
            suggestions.append("Add tools to give your assistant specific capabilities")
        
        # Check for LangGraph/Research configuration
        yaml_lower = yaml_content.lower()
        if "ngrok-free.app" in yaml_content or "8082" in yaml_content:
            validation_results.append("🔬 LangGraph Research Assistant detected")
        elif "8081" in yaml_content or "tesseract" in yaml_lower:
            validation_results.append("🔧 Tesseract Workflow Engine detected")
        
        return {
            "success": True,
            "message": "Configuration validation successful",
            "configInfo": config_info,
            "validation": validation_results,
            "warnings": warnings,
            "suggestions": suggestions,
            "stats": {
                "lineCount": len(yaml_content.split('\n')),
                "characterCount": len(yaml_content),
                "toolCount": config_info.get("toolCount", 0),
                "hasRequiredFields": config_info.get("hasSystemPrompt", False) and config_info.get("hasFirstMessage", False)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Validation error",
            "error": str(e),
            "suggestions": [
                "Check the YAML syntax and structure",
                "Ensure all required fields are present",
                "Verify the configuration follows the expected format"
            ]
        }

# =================== VAPI ASSISTANT MANAGEMENT ENDPOINTS ===================

class VapiAssistantRequest(BaseModel):
    user_id: str
    name: Optional[str] = None

class VapiAssistantResponse(BaseModel):
    assistant_id: str
    name: str
    status: str
    message: str

@app.post("/vapi/assistant", response_model=VapiAssistantResponse)
async def create_vapi_assistant(request: VapiAssistantRequest):
    """Create a new Vapi assistant with current configuration"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        if not PUBLIC_SERVER_URL or "localhost" in PUBLIC_SERVER_URL:
            raise HTTPException(status_code=400, detail="PUBLIC_SERVER_URL must be set to a public ngrok URL")
        
        # Import orchestrator functionality
        from orchestrator import VapiOrchestrator
        
        orchestrator = VapiOrchestrator(VAPI_API_KEY, PUBLIC_SERVER_URL)
        result = await orchestrator.create_assistant(request.user_id)
        
        return VapiAssistantResponse(
            assistant_id=result["id"],
            name=result["name"],
            status="success",
            message=f"Assistant created successfully for user {request.user_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Vapi assistant: {str(e)}")

@app.get("/vapi/assistants")
async def list_vapi_assistants():
    """List all Vapi assistants"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        from orchestrator import VapiOrchestrator
        
        orchestrator = VapiOrchestrator(VAPI_API_KEY, PUBLIC_SERVER_URL)
        result = await orchestrator.list_assistants()
        
        # Handle the fact that Vapi API returns a list directly, not a dict with "data" key
        if isinstance(result, list):
            assistants = result
        else:
            assistants = result.get("data", [])
        
        return {
            "assistants": assistants,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Vapi assistants: {str(e)}")

@app.delete("/vapi/assistant/{assistant_id}")
async def delete_vapi_assistant(assistant_id: str):
    """Delete a Vapi assistant"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        from orchestrator import VapiOrchestrator
        
        orchestrator = VapiOrchestrator(VAPI_API_KEY, PUBLIC_SERVER_URL)
        success = await orchestrator.delete_assistant(assistant_id)
        
        if success:
            return {
                "message": f"Assistant {assistant_id} deleted successfully",
                "status": "success"
            }
        else:
            raise HTTPException(status_code=404, detail="Assistant not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete Vapi assistant: {str(e)}")

@app.get("/vapi/tools")
async def list_vapi_tools():
    """List all Vapi tools"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        from orchestrator import VapiOrchestrator
        
        orchestrator = VapiOrchestrator(VAPI_API_KEY, PUBLIC_SERVER_URL)
        result = await orchestrator.list_tools()
        
        # Handle the fact that Vapi API returns a list directly, not a dict with "data" key
        if isinstance(result, list):
            tools = result
        else:
            tools = result.get("data", [])
        
        return {
            "tools": tools,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Vapi tools: {str(e)}")

@app.patch("/vapi/assistant/{assistant_id}")
async def update_vapi_assistant(assistant_id: str):
    """Update a Vapi assistant configuration to remove server conflicts"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        from orchestrator import VapiOrchestrator
        
        orchestrator = VapiOrchestrator(VAPI_API_KEY, PUBLIC_SERVER_URL)
        
        # Get current assistant
        current_assistant = await orchestrator.get_assistant(assistant_id)
        
        # Remove the server configuration to avoid conflicts with tool-level servers
        update_data = {
            "name": current_assistant["name"],
            "model": current_assistant["model"],
            "voice": current_assistant["voice"],
            "firstMessage": current_assistant["firstMessage"],
            "server": None  # Explicitly remove server config
        }
        
        # Make the update via direct API call to remove server config
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"https://api.vapi.ai/assistant/{assistant_id}",
                    headers={
                        "Authorization": f"Bearer {VAPI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=update_data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "message": f"Assistant {assistant_id} updated successfully - removed server config conflict",
                    "status": "success",
                    "assistant": result
                }
                
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"Failed to update assistant: {str(e)}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Vapi assistant: {str(e)}")

# =================== SYSTEM STATUS ENDPOINTS ===================

@app.get("/status")
async def get_system_status():
    """Get comprehensive system status with service registry information"""
    try:
        registry = get_service_registry()
        
        # Get service health status
        health_status = await registry.health_check_all()
        
        # Get deployment information
        deployment_info = registry.get_deployment_info()
        
        # Check environment variables
        environment = {
            "public_server_url": PUBLIC_SERVER_URL,
            "vapi_api_key_set": bool(VAPI_API_KEY),
            "ngrok_active": not ("localhost" in PUBLIC_SERVER_URL),
        }
        
        # Check configuration
        config_status = {
            "tools_count": len(config.get("tools", [])),
            "assistant_configured": bool(config.get("assistant")),
        }
        
        return {
            "services": health_status,
            "deployment": deployment_info,
            "environment": environment,
            "configuration": config_status,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@app.get("/vapi/public-key")
async def get_vapi_public_key():
    """Get Vapi public key for web SDK"""
    try:
        if not VAPI_PUBLIC_KEY:
            raise HTTPException(status_code=400, detail="VAPI_PUBLIC_KEY not set in environment variables")
        
        return {
            "public_key": VAPI_PUBLIC_KEY,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get public key: {str(e)}")

@app.post("/vapi/assistant/web-optimized")
async def create_web_optimized_assistant():
    """Create a Vapi assistant optimized for web calls with inline tools"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        # Create Vapi-compatible assistant configuration
        vapi_assistant_config = {
            "name": "Tesseract Web Assistant",
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "system",
                    "content": "You are a specialized AI assistant for the Tesseract system. Your goal is to accurately trigger the correct tool based on the user's request.\nCRITICAL RULES: 1. If the user's request clearly matches a specific workflow tool like 'triggerFinancialAnalysisWorkflow', ask for any missing parameters and then call that tool. 2. For ALL OTHER requests, including simple questions, greetings, or ambiguous commands, you MUST use the 'processGeneralRequest' tool. Do not try to answer yourself. 3. The user's ID is demo_user_123.\nExample 1: User says \"I need a financial analysis of Tesla\". You should ask clarifying questions for 'analysis_type', then call 'triggerFinancialAnalysisWorkflow'. Example 2: User says \"What's the weather?\" or \"Hello there\". You MUST call 'processGeneralRequest'.\n"
                }],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "triggerFinancialAnalysisWorkflow",
                            "description": "Use this specific tool to run a multi-step financial analysis on a company. Requires the company name and the type of analysis.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "user_id": {
                                        "type": "string",
                                        "description": "The user's unique ID."
                                    },
                                    "company_name": {
                                        "type": "string",
                                        "description": "The name of the company to analyze, e.g., 'Tesla Inc'."
                                    },
                                    "analysis_type": {
                                        "type": "string",
                                        "description": "The type of analysis to run, e.g., 'credit_risk', 'standard_review'."
                                    }
                                },
                                "required": ["user_id", "company_name", "analysis_type"]
                            }
                        }
                    },
                    {
                        "type": "function", 
                        "function": {
                            "name": "processGeneralRequest",
                            "description": "A general-purpose tool for all other requests, simple questions, or ambiguous commands that do not fit a specific workflow.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "user_id": {
                                        "type": "string",
                                        "description": "The user's unique ID."
                                    },
                                    "user_input": {
                                        "type": "string",
                                        "description": "The user's full, verbatim request."
                                    }
                                },
                                "required": ["user_id", "user_input"]
                            }
                        }
                    }
                ]
            },
            "voice": {
                "provider": "playht",
                "voiceId": "jennifer-playht"
            },
            "firstMessage": "Tesseract system online. How can I assist you?",
            "server": {
                "url": f"{PUBLIC_SERVER_URL}/webhook/tool-call"
            }
        }
        
        # Create the assistant via direct API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vapi.ai/assistant",
                headers={
                    "Authorization": f"Bearer {VAPI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=vapi_assistant_config,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "assistant_id": result["id"],
                "name": result["name"],
                "message": "Web-optimized assistant created successfully with inline tools",
                "status": "success",
                "assistant": result
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create web-optimized assistant: {str(e)}")

@app.post("/vapi/assistant/dynamic")
async def create_dynamic_assistant():
    """Create a Vapi assistant dynamically based on current YAML configuration using orchestrator"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        # Use the orchestrator for consistent assistant creation
        from orchestrator import VapiOrchestrator
        
        orchestrator = VapiOrchestrator(VAPI_API_KEY, PUBLIC_SERVER_URL)
        result = await orchestrator.create_assistant("dynamic_user")
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create assistant via orchestrator")
        
        # Load current configuration for response details
        current_config = load_config()
        assistant_config = current_config["assistant"]
        tools_config = current_config["tools"]
        
        return {
            "assistant_id": result["id"],
            "name": result["name"],
            "message": f"Dynamic assistant created successfully with webhook support",
            "status": "success",
            "config_based_on": {
                "agent_name": assistant_config["name"],
                "tools_count": len(tools_config),
                "model_provider": assistant_config["model"]["provider"],
                "voice_provider": assistant_config["voice"]["provider"]
            },
            "webhook_url": f"{PUBLIC_SERVER_URL}/webhook/tool-call",
            "assistant": result
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dynamic assistant: {str(e)}")

@app.get("/vapi/assistant/current")
async def get_current_assistant_id():
    """Get or create the current assistant ID based on configuration"""
    try:
        # For now, we'll create a new assistant each time
        # In production, you might want to cache this or store it
        result = await create_dynamic_assistant()
        return {
            "assistant_id": result["assistant_id"],
            "status": "success",
            "message": "Current assistant ready for voice calls"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current assistant: {str(e)}")

# =================== SERVICE STATUS PROXY ENDPOINTS ===================

@app.get("/service-status/{service_id}")
async def check_service_status(service_id: str):
    """Check the status of a specific service by ID"""
    try:
        service_configs = {
            "langgraph": {
                "url": "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/health",
                "name": "LangGraph Research Assistant"
            },
            "tesseract": {
                "url": "http://localhost:8081/",
                "name": "Tesseract Workflow Engine"
            },
            "vapi_forge": {
                "url": "http://localhost:8000/",
                "name": "Vapi Agent Forge"
            }
        }
        
        if service_id not in service_configs:
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
        
        service_config = service_configs[service_id]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(service_config["url"], timeout=10.0)
            response.raise_for_status()
            
            # Try to parse as JSON, fallback to text
            try:
                data = response.json()
                message = data.get("message") or data.get("status") or "Running"
            except:
                message = "Running"
            
            return {
                "service_id": service_id,
                "name": service_config["name"],
                "online": True,
                "message": message,
                "status": "success"
            }
            
    except httpx.TimeoutException:
        return {
            "service_id": service_id,
            "name": service_configs.get(service_id, {}).get("name", "Unknown Service"),
            "online": False,
            "error": "Service timeout - check if service is running",
            "status": "error"
        }
    except httpx.HTTPError as e:
        return {
            "service_id": service_id,
            "name": service_configs.get(service_id, {}).get("name", "Unknown Service"),
            "online": False,
            "error": f"HTTP error: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        return {
            "service_id": service_id,
            "name": service_configs.get(service_id, {}).get("name", "Unknown Service"),
            "online": False,
            "error": str(e),
            "status": "error"
        }

@app.get("/service-status")
async def check_all_services_status():
    """Check the status of all known services"""
    services = ["langgraph", "tesseract", "vapi_forge"]
    results = {}
    
    for service_id in services:
        try:
            # Call the individual service status endpoint
            result = await check_service_status(service_id)
            results[service_id] = result
        except Exception as e:
            results[service_id] = {
                "service_id": service_id,
                "online": False,
                "error": str(e),
                "status": "error"
            }
    
    return {
        "services": results,
        "status": "success",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }

# =================== SERVICE REGISTRY ENDPOINTS ===================

@app.get("/services")
async def get_services():
    """Get all registered services and their status"""
    try:
        registry = get_service_registry()
        deployment_info = registry.get_deployment_info()
        health_status = await registry.health_check_all()
        
        return {
            "deployment_info": deployment_info,
            "services": health_status,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

@app.get("/services/{service_name}")
async def get_service_status(service_name: str):
    """Get status of a specific service"""
    try:
        registry = get_service_registry()
        health_status = await registry.health_check(service_name)
        
        return {
            "service": service_name,
            "health": health_status,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")

@app.get("/services/config/template")
async def get_services_config_template():
    """Get a services.yaml template for companies to customize"""
    try:
        registry = get_service_registry()
        template = registry.export_config_template()
        
        return {
            "template": template,
            "instructions": {
                "file_location": "Create a 'services.yaml' file in your backend directory",
                "environment_variables": "Alternatively, set environment variables like LANGGRAPH_SERVICE_URL",
                "priority": "Environment variables override services.yaml, which overrides defaults"
            },
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")

@app.post("/services/reload")
async def reload_services():
    """Reload service registry configuration"""
    try:
        registry = get_service_registry()
        registry.load_services()
        
        # Also reload tool executor with new service registry
        reload_tool_executor()
        
        return {
            "message": "Service registry reloaded successfully",
            "deployment_info": registry.get_deployment_info(),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload services: {str(e)}")

# =================== ENHANCED STATUS ENDPOINTS ===================

@app.get("/status")
async def get_system_status():
    """Get comprehensive system status with service registry information"""
    try:
        registry = get_service_registry()
        
        # Get service health status
        health_status = await registry.health_check_all()
        
        # Get deployment information
        deployment_info = registry.get_deployment_info()
        
        # Check environment variables
        environment = {
            "public_server_url": PUBLIC_SERVER_URL,
            "vapi_api_key_set": bool(VAPI_API_KEY),
            "ngrok_active": not ("localhost" in PUBLIC_SERVER_URL),
        }
        
        # Check configuration
        config_status = {
            "tools_count": len(config.get("tools", [])),
            "assistant_configured": bool(config.get("assistant")),
        }
        
        return {
            "services": health_status,
            "deployment": deployment_info,
            "environment": environment,
            "configuration": config_status,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

# =================== ENHANCED CONFIGURATION ENDPOINTS ===================

@app.get("/config/resolved")
async def get_resolved_config():
    """Get configuration with resolved URLs for debugging"""
    try:
        registry = get_service_registry()
        resolved_config = config.copy()
        
        # Resolve all tool URLs
        for tool in resolved_config.get("tools", []):
            if "action" in tool and "url" in tool["action"]:
                original_url = tool["action"]["url"]
                resolved_url = registry.resolve_tool_url({"url": original_url})
                tool["action"]["resolved_url"] = resolved_url
                tool["action"]["original_url"] = original_url
        
        return {
            "config": resolved_config,
            "deployment_info": registry.get_deployment_info(),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve configuration: {str(e)}")

# Add interaction logging endpoint
@app.post("/users/{user_id}/interactions")
async def log_user_interaction(user_id: int, interaction_data: dict):
    """Log user interaction"""
    try:
        await log_interaction(
            user_id=user_id,
            voice_agent_id=interaction_data.get("voice_agent_id"),
            interaction_type=interaction_data.get("interaction_type"),
            content=interaction_data.get("content")
        )
        return {"status": "success", "message": "Interaction logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log interaction: {str(e)}")

# Load configuration
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

def save_config(config_data: dict):
    """Save configuration to config.yaml file"""
    with open("config.yaml", "w") as file:
        yaml.dump(config_data, file, default_flow_style=False, indent=2)

def reload_tool_executor():
    """Reload the tool executor with new configuration"""
    global tool_executor, config
    config = load_config()
    tool_executor = UserToolExecutor(user_id=1, config=config)

config = load_config()

# Pydantic models
class ToolCallData(BaseModel):
    name: str
    parameters: Dict[str, Any]

class VapiToolCall(BaseModel):
    message: Dict[str, Any]
    call: Dict[str, Any]

class VapiResponse(BaseModel):
    result: str

class AssistantConfig(BaseModel):
    name: str
    model: Dict[str, Any]
    voice: Dict[str, str]
    firstMessage: str
    tools: List[Dict[str, Any]]

class ToolExecutor:
    """Handles execution of tools defined in config.yaml with dynamic URL resolution"""
    
    def __init__(self, config: Dict[str, Any], service_registry: ServiceRegistry):
        self.config = config
        self.service_registry = service_registry
        self.tools = {tool["name"]: tool for tool in config["tools"]}
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute a tool with given parameters using dynamic URL resolution
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Response string formatted according to tool configuration
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_config = self.tools[tool_name]
        action_config = tool_config["action"]
        
        # Prepare the API call with dynamic URL resolution
        method = action_config["method"]
        url_template = action_config["url"]
        
        # Resolve URL using service registry
        resolved_url = self.service_registry.resolve_tool_url({"url": url_template})
        
        # Replace URL parameters
        url = self._replace_placeholders(resolved_url, parameters)
        
        # Prepare request body
        json_body = None
        if "json_body" in action_config:
            json_body = self._replace_placeholders_in_dict(action_config["json_body"], parameters)
        
        # Make the API call
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(url, json=json_body)
                elif method.upper() == "GET":
                    response = await client.get(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                response_data = response.json()
                
                # Format the response according to tool configuration
                return self._format_response(tool_config, response_data, parameters)
                
            except httpx.HTTPError as e:
                raise Exception(f"API call failed: {str(e)}")
    
    def _replace_placeholders(self, template: str, parameters: Dict[str, Any]) -> str:
        """Replace {parameter} placeholders in strings"""
        for key, value in parameters.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
    
    def _replace_placeholders_in_dict(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively replace placeholders in dictionary structures"""
        if isinstance(data, dict):
            return {k: self._replace_placeholders_in_dict(v, parameters) for k, v in data.items()}
        elif isinstance(data, str):
            return self._replace_placeholders(data, parameters)
        else:
            return data
    
    def _format_response(self, tool_config: Dict[str, Any], response_data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Format the response according to tool configuration"""
        action_config = tool_config["action"]
        
        # Check if there's a response_template
        if "response_template" in action_config:
            template = action_config["response_template"]
            # Replace placeholders with response data
            for key, value in response_data.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        
        # Check if there's a response_path for extracting specific data
        elif "response_path" in action_config:
            path = action_config["response_path"]
            if path in response_data:
                return str(response_data[path])
            else:
                raise ValueError(f"Response path '{path}' not found in API response")
        
        # Default: return the entire response as JSON string
        else:
            return json.dumps(response_data, indent=2)

# Initialize tool executor
tool_executor = ToolExecutor(config, get_service_registry())

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Vapi Agent Forge is running",
        "status": "healthy",
        "public_url": PUBLIC_SERVER_URL
    }

@app.get("/health")
async def health_check():
    """Dedicated health check endpoint"""
    return {
        "message": "Vapi Agent Forge is running",
        "status": "healthy",
        "public_url": PUBLIC_SERVER_URL
    }

@app.post("/users/{user_id}/services/langgraph")
async def configure_langgraph_service(user_id: int, service_url: str = "http://localhost:8001"):
    """
    Configure LangGraph service for a user (helper endpoint)
    
    Args:
        user_id: User ID
        service_url: URL of the LangGraph service
    """
    service_config = UserServiceConfig(
        service_name="langgraph",
        service_url=service_url,
        health_path="/health",
        timeout=30,
        required=True
    )
    
    return await configure_user_service(user_id, service_config)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 