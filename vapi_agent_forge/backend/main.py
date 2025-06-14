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
    tool_executor = ToolExecutor(config)

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
    """Handles execution of tools defined in config.yaml"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = {tool["name"]: tool for tool in config["tools"]}
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute a tool with given parameters
        
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
        
        # Prepare the API call
        method = action_config["method"]
        url_template = action_config["url"]
        
        # Replace URL parameters
        url = self._replace_placeholders(url_template, parameters)
        
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
tool_executor = ToolExecutor(config)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Vapi Agent Forge is running",
        "status": "healthy",
        "public_url": PUBLIC_SERVER_URL
    }

@app.post("/webhook/tool-call")
async def handle_tool_call(request: Request):
    """
    Handle Vapi tool calls and execute the appropriate tool
    
    Args:
        request: Raw FastAPI request to inspect the actual format
        
    Returns:
        VapiResponse with the result
    """
    print(f"\n{'='*80}")
    print(f"🎯 WEBHOOK TOOL CALL RECEIVED at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Request method: {request.method}")
    print(f"🎯 Request URL: {request.url}")
    print(f"🎯 Request headers: {dict(request.headers)}")
    print(f"{'='*80}")
    
    try:
        # Get the raw JSON data to see what Vapi is actually sending
        raw_data = await request.json()
        print(f"🔍 Raw webhook data from Vapi: {json.dumps(raw_data, indent=2)}")
        
        # Check message type
        message = raw_data.get("message", {})
        message_type = message.get("type")
        
        print(f"📋 Message type: {message_type}")
        
        # Ignore end-of-call reports and other non-tool messages silently
        if message_type in ["end-of-call-report", "conversation-update", "status-update"]:
            return {"result": "Non-tool message processed"}
        
        # Look for tool calls in multiple possible locations
        tool_calls = []
        
        # Check for Vapi's official tool call format
        if "toolCallList" in message:
            tool_call_list = message["toolCallList"]
            print(f"🔧 Found {len(tool_call_list)} tool calls in message.toolCallList")
            # Convert Vapi format to our expected format
            for tool_call in tool_call_list:
                # toolCallList items have structure: {id, type, function: {name, arguments}}
                function_data = tool_call.get("function", {})
                tool_calls.append({
                    "id": tool_call.get("id"),
                    "function": {
                        "name": function_data.get("name"),
                        "arguments": function_data.get("arguments", {})
                    }
                })
        
        # Check for direct tool call format (our test format)
        elif "toolCalls" in message:
            tool_calls = message["toolCalls"]
            print(f"🔧 Found {len(tool_calls)} tool calls in message.toolCalls")
        
        # Check for tool call in root level
        elif "toolCall" in raw_data:
            tool_calls = [raw_data["toolCall"]]
            print("🔧 Found single tool call in root.toolCall")
        
        # Check for function call format
        elif "functionCall" in message:
            func_call = message["functionCall"]
            tool_calls = [{
                "function": {
                    "name": func_call.get("name"),
                    "arguments": func_call.get("parameters", {})
                }
            }]
            print("🔧 Found function call, converted to tool call format")
        
        # Check if this is a single tool execution request
        elif message_type == "tool-call" or "function" in raw_data:
            # Handle single tool call format
            if "function" in raw_data:
                tool_calls = [{"function": raw_data["function"]}]
                print("🔧 Found function in root level")
        
        # NEW: Check for tool calls in conversation or other nested locations
        elif "conversation" in message:
            # Look for tool calls in the conversation messages
            for conv_item in message["conversation"]:
                if conv_item.get("role") == "tool_calls" and "toolCalls" in conv_item:
                    tool_calls = conv_item["toolCalls"]
                    print(f"🔧 Found {len(tool_calls)} tool calls in conversation.toolCalls")
                    break
        
        # NEW: Check if we have a function call request in different formats
        if not tool_calls:
            # Look for any field that might contain function/tool information
            for key, value in raw_data.items():
                if isinstance(value, dict):
                    if "function" in value or "name" in value:
                        print(f"🔍 Found potential tool call in {key}: {value}")
                        if "function" in value:
                            tool_calls = [{"function": value["function"]}]
                            break
                        elif "name" in value and "arguments" in value:
                            tool_calls = [{"function": value}]
                            break
        
        if not tool_calls:
            # Log what we have for debugging
            print("⚠️ No tool calls found in webhook data")
            print("🔍 Available keys in message:", list(message.keys()))
            print("🔍 Available keys in raw_data:", list(raw_data.keys()))
            # Don't log error for non-tool messages, just return quietly
            return {"result": "No tool calls to process"}
        
        # Process the first tool call (Vapi typically sends one at a time)
        tool_call = tool_calls[0]
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        
        # Extract tool call ID for Vapi's response format
        tool_call_id = None
        if "toolCallList" in message and message["toolCallList"]:
            tool_call_id = message["toolCallList"][0].get("id")
        elif "id" in tool_call:
            tool_call_id = tool_call.get("id")
        
        if not tool_name:
            print("⚠️ No tool name found in function")
            print(f"🔍 Tool call structure: {json.dumps(tool_call, indent=2)}")
            print(f"🔍 Function structure: {json.dumps(function, indent=2)}")
            return {"error": "No tool name provided"}
        
        # Parse arguments (might be JSON string or dict)
        raw_arguments = function.get("arguments", {})
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                print(f"❌ Failed to parse JSON arguments: {raw_arguments}")
                return {"error": "Invalid JSON arguments"}
        else:
            arguments = raw_arguments
        
        print(f"🔧 Extracted tool: {tool_name}, parameters: {json.dumps(arguments, indent=2)}")
        
        # Execute the tool dynamically using the ToolExecutor
        result = await tool_executor.execute_tool(tool_name, arguments)
        
        print(f"✅ Tool execution result: {result}")
        
        # Return in Vapi's expected format with results array and toolCallId
        if tool_call_id:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": result
                }]
            }
        else:
            # Fallback to simple format if no toolCallId
            return {"result": result}
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {"result": f"Error: Invalid JSON - {str(e)}"}
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
    """Get comprehensive system status"""
    try:
        # Check Tesseract Engine
        tesseract_status = {"online": False, "error": None}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8081/", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    tesseract_status = {"online": True, "message": data.get("message", "Running")}
        except Exception as e:
            tesseract_status = {"online": False, "error": str(e)}
        
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
            "tesseract_engine": tesseract_status,
            "vapi_forge": {"online": True, "message": "Running"},
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
    """Create a Vapi assistant dynamically based on current YAML configuration"""
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=400, detail="VAPI_API_KEY not set in environment variables")
        
        # Load current configuration
        current_config = load_config()
        assistant_config = current_config["assistant"]
        tools_config = current_config["tools"]
        
        # Convert our YAML tools to Vapi format
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
        
        # Create Vapi assistant configuration
        vapi_assistant_config = {
            "name": assistant_config["name"],
            "model": {
                "provider": assistant_config["model"]["provider"],
                "model": assistant_config["model"]["model"],
                "messages": [{
                    "role": "system",
                    "content": assistant_config["model"].get("system_prompt_template", "You are a helpful AI assistant.")
                }],
                "tools": vapi_tools
            },
            "voice": assistant_config["voice"],
            "firstMessage": assistant_config["firstMessage"],
            "server": {
                "url": f"{PUBLIC_SERVER_URL}/webhook/tool-call"
            }
        }
        
        # Create the assistant via Vapi API
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
            
    except httpx.HTTPError as e:
        error_detail = f"HTTP error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                error_detail = f"Vapi API error: {error_data}"
            except:
                error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        raise HTTPException(status_code=500, detail=f"Failed to create dynamic assistant: {error_detail}")
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 