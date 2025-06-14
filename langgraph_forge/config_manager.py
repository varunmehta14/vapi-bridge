#!/usr/bin/env python3
"""
Configuration Manager for LangGraph Research & Content Assistant
Handles YAML configuration parsing and validation for voice agents.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import structlog

logger = structlog.get_logger()

class ModelConfig(BaseModel):
    """Model configuration"""
    provider: str = "google"
    model: str = "gemini-1.5-flash"
    system_prompt_template: Optional[str] = None

class VoiceConfig(BaseModel):
    """Voice configuration"""
    provider: str = "playht"
    voiceId: str = "jennifer-playht"

class ToolParameter(BaseModel):
    """Tool parameter definition"""
    type: str
    description: str

class ToolParameters(BaseModel):
    """Tool parameters schema"""
    type: str = "object"
    properties: Dict[str, ToolParameter]
    required: List[str] = []

class ToolAction(BaseModel):
    """Tool action configuration"""
    type: str = "api_call"
    method: str = "POST"
    url: str
    json_body: Optional[Dict[str, Any]] = None
    response_path: Optional[str] = None
    response_template: Optional[str] = None

class Tool(BaseModel):
    """Tool definition"""
    name: str
    description: str
    parameters: ToolParameters
    action: ToolAction

class AssistantConfig(BaseModel):
    """Assistant configuration"""
    name: str
    model: ModelConfig
    voice: Optional[VoiceConfig] = None
    firstMessage: Optional[str] = None

class AgentConfig(BaseModel):
    """Complete agent configuration"""
    assistant: AssistantConfig
    tools: List[Tool] = []

class ConfigManager:
    """Manages YAML configurations for research and content agents"""
    
    def __init__(self):
        self.config_dir = os.getenv("CONFIG_DIR", "./configs")
        self.default_config = self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default research assistant configuration"""
        return {
            "assistant": {
                "name": "Research & Content Assistant",
                "model": {
                    "provider": "google",
                    "model": "gemini-1.5-flash",
                    "system_prompt_template": """You are an intelligent Research & Content Assistant powered by LangGraph workflows and Google Gemini AI. 

Your primary capabilities:
1. **Research Topics**: Conduct comprehensive research using multiple sources (web search, Wikipedia, academic sources)
2. **Generate Content**: Create high-quality articles, blog posts, reports, and other content
3. **Answer Questions**: Provide detailed, well-researched answers with source citations
4. **Summarize Information**: Distill complex information into clear, actionable insights

When users ask for research or content generation:
- Use the appropriate tool (research_topic or generate_content)
- Always provide comprehensive, accurate information
- Include sources and citations when possible
- Tailor your response to the user's specific needs

Be helpful, accurate, and thorough in all interactions. Leverage Google Gemini's advanced reasoning capabilities to provide insightful analysis."""
                },
                "voice": {
                    "provider": "playht",
                    "voiceId": "jennifer-playht"
                },
                "firstMessage": "Hello! I'm your Research & Content Assistant powered by Google Gemini. I can help you research any topic, generate high-quality content, answer complex questions, and provide detailed analysis. What would you like to explore today?"
            },
            "tools": [
                {
                    "name": "research_topic",
                    "description": "Research a topic comprehensively using multiple sources and provide detailed analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The research query or topic to investigate"
                            },
                            "research_type": {
                                "type": "string",
                                "description": "Type of research: comprehensive, quick, or deep",
                                "enum": ["comprehensive", "quick", "deep"]
                            },
                            "max_sources": {
                                "type": "integer",
                                "description": "Maximum number of sources to research (1-10)",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "include_summary": {
                                "type": "boolean",
                                "description": "Whether to include a comprehensive summary"
                            }
                        },
                        "required": ["query"]
                    },
                    "action": {
                        "type": "api_call",
                        "method": "POST",
                        "url": "http://localhost:8082/research",
                        "json_body": {
                            "query": "{query}",
                            "research_type": "{research_type}",
                            "max_sources": "{max_sources}",
                            "include_summary": "{include_summary}"
                        },
                        "response_template": "Research started for: {query}. I'll analyze multiple sources using Google Gemini and provide you with comprehensive findings. Job ID: {job_id}"
                    }
                },
                {
                    "name": "generate_content",
                    "description": "Generate high-quality content such as articles, blog posts, reports, or marketing copy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The topic or subject for content generation"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "Type of content to generate",
                                "enum": ["article", "blog", "report", "summary", "marketing", "social", "email"]
                            },
                            "tone": {
                                "type": "string",
                                "description": "Tone of the content",
                                "enum": ["professional", "casual", "academic", "creative", "persuasive", "friendly"]
                            },
                            "length": {
                                "type": "string",
                                "description": "Length of the content",
                                "enum": ["short", "medium", "long"]
                            }
                        },
                        "required": ["topic"]
                    },
                    "action": {
                        "type": "api_call",
                        "method": "POST",
                        "url": "http://localhost:8082/generate-content",
                        "json_body": {
                            "topic": "{topic}",
                            "content_type": "{content_type}",
                            "tone": "{tone}",
                            "length": "{length}"
                        },
                        "response_template": "Content generation started for: {topic}. I'll create engaging {content_type} content with a {tone} tone using Google Gemini. Job ID: {job_id}"
                    }
                }
            ]
        }
    
    def load_config(self, config_path: str) -> AgentConfig:
        """Load and validate agent configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
            
            # Validate configuration
            config = AgentConfig(**config_data)
            
            logger.info("Configuration loaded successfully", config_path=config_path)
            return config
            
        except Exception as e:
            logger.error("Failed to load configuration", config_path=config_path, error=str(e))
            raise
    
    def save_config(self, config: AgentConfig, config_path: str):
        """Save agent configuration to YAML file"""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Convert to dict and save
            config_dict = config.dict()
            
            with open(config_path, 'w') as file:
                yaml.dump(config_dict, file, default_flow_style=False, allow_unicode=True)
            
            logger.info("Configuration saved successfully", config_path=config_path)
            
        except Exception as e:
            logger.error("Failed to save configuration", config_path=config_path, error=str(e))
            raise
    
    def validate_yaml_string(self, yaml_string: str) -> Dict[str, Any]:
        """Validate YAML string and return parsed configuration"""
        try:
            # Parse YAML
            config_data = yaml.safe_load(yaml_string)
            
            if not config_data:
                raise ValueError("Empty configuration")
            
            # Validate against schema
            config = AgentConfig(**config_data)
            
            return {
                "valid": True,
                "config": config.dict(),
                "message": "Configuration is valid"
            }
            
        except yaml.YAMLError as e:
            return {
                "valid": False,
                "error": f"YAML parsing error: {str(e)}",
                "message": "Invalid YAML format"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "Configuration validation failed"
            }
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get the default research assistant configuration"""
        return self.default_config.copy()
    
    def get_research_tools(self) -> List[Dict[str, Any]]:
        """Get available research and content generation tools"""
        return [
            {
                "name": "research_topic",
                "description": "Research any topic using multiple sources",
                "categories": ["research", "information", "analysis"],
                "parameters": ["query", "research_type", "max_sources", "include_summary"]
            },
            {
                "name": "generate_content",
                "description": "Generate high-quality content",
                "categories": ["content", "writing", "marketing"],
                "parameters": ["topic", "content_type", "tone", "length"]
            }
        ]
    
    def create_vapi_compatible_config(self, config: AgentConfig) -> Dict[str, Any]:
        """Convert internal config to Vapi-compatible format"""
        try:
            vapi_config = {
                "name": config.assistant.name,
                "model": {
                    "provider": config.assistant.model.provider,
                    "model": config.assistant.model.model,
                    "systemMessage": config.assistant.model.system_prompt_template
                },
                "voice": {
                    "provider": config.assistant.voice.provider,
                    "voiceId": config.assistant.voice.voiceId
                } if config.assistant.voice else None,
                "firstMessage": config.assistant.firstMessage,
                "tools": []
            }
            
            # Convert tools to Vapi format
            for tool in config.tools:
                vapi_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters.dict()
                    },
                    "server": {
                        "url": tool.action.url,
                        "method": tool.action.method
                    }
                }
                vapi_config["tools"].append(vapi_tool)
            
            return vapi_config
            
        except Exception as e:
            logger.error("Failed to create Vapi-compatible config", error=str(e))
            raise
    
    def extract_server_urls(self, config: AgentConfig) -> List[str]:
        """Extract unique server URLs from configuration"""
        urls = set()
        
        for tool in config.tools:
            if tool.action.url:
                urls.add(tool.action.url)
        
        return list(urls)
    
    def validate_server_connectivity(self, config: AgentConfig) -> Dict[str, Any]:
        """Validate that all configured servers are reachable"""
        import httpx
        import asyncio
        
        async def check_url(url: str) -> Dict[str, Any]:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url.replace("/research", "/health").replace("/generate-content", "/health"))
                    return {
                        "url": url,
                        "status": "reachable" if response.status_code == 200 else "error",
                        "status_code": response.status_code
                    }
            except Exception as e:
                return {
                    "url": url,
                    "status": "unreachable",
                    "error": str(e)
                }
        
        async def check_all_urls():
            urls = self.extract_server_urls(config)
            tasks = [check_url(url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        try:
            results = asyncio.run(check_all_urls())
            return {
                "connectivity_check": True,
                "servers": results,
                "all_reachable": all(r.get("status") == "reachable" for r in results if isinstance(r, dict))
            }
        except Exception as e:
            return {
                "connectivity_check": False,
                "error": str(e)
            } 