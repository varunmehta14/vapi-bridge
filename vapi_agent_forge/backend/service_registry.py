#!/usr/bin/env python3
"""
Service Registry for Dynamic URL Resolution
Enables companies to deploy their own services with flexible URL configuration
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import httpx
import asyncio
from pathlib import Path

@dataclass
class ServiceEndpoint:
    """Represents a service endpoint with health check capabilities"""
    name: str
    base_url: str
    health_path: str = "/health"
    timeout: int = 5
    required: bool = True
    
    @property
    def health_url(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.health_path}"
    
    def is_localhost(self) -> bool:
        """Check if this is a localhost URL"""
        parsed = urlparse(self.base_url)
        return parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']

class ServiceRegistry:
    """
    Manages service discovery and URL resolution for different deployment environments
    
    Supports:
    - Environment variables for service URLs
    - Service discovery files
    - Automatic localhost detection
    - Health checking
    - Fallback mechanisms
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.services: Dict[str, ServiceEndpoint] = {}
        self.config_path = config_path or "services.yaml"
        self.load_services()
    
    def load_services(self):
        """Load service configurations from multiple sources"""
        # 1. Load from environment variables
        self._load_from_environment()
        
        # 2. Load from configuration file
        self._load_from_config()
        
        # 3. Apply defaults for missing services
        self._apply_defaults()
    
    def _load_from_environment(self):
        """Load service URLs from environment variables"""
        env_mappings = {
            'LANGGRAPH_SERVICE_URL': 'langgraph',
            'TESSERACT_SERVICE_URL': 'tesseract',
            'RESEARCH_SERVICE_URL': 'research',
            'CONTENT_SERVICE_URL': 'content',
            'WORKFLOW_SERVICE_URL': 'workflow',
            'BACKEND_SERVICE_URL': 'backend',
            'PUBLIC_SERVER_URL': 'public_backend'
        }
        
        for env_var, service_name in env_mappings.items():
            url = os.getenv(env_var)
            if url:
                self.services[service_name] = ServiceEndpoint(
                    name=service_name,
                    base_url=url,
                    health_path=self._get_health_path(service_name)
                )
    
    def _load_from_config(self):
        """Load service configurations from YAML file"""
        if not Path(self.config_path).exists():
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            services_config = config.get('services', {})
            for service_name, service_config in services_config.items():
                if isinstance(service_config, str):
                    # Simple URL string
                    self.services[service_name] = ServiceEndpoint(
                        name=service_name,
                        base_url=service_config,
                        health_path=self._get_health_path(service_name)
                    )
                elif isinstance(service_config, dict):
                    # Full configuration
                    self.services[service_name] = ServiceEndpoint(
                        name=service_name,
                        base_url=service_config['url'],
                        health_path=service_config.get('health_path', self._get_health_path(service_name)),
                        timeout=service_config.get('timeout', 5),
                        required=service_config.get('required', True)
                    )
        except Exception as e:
            print(f"Warning: Failed to load services config: {e}")
    
    def _apply_defaults(self):
        """Apply default localhost URLs for missing services"""
        defaults = {
            'langgraph': ServiceEndpoint('langgraph', 'http://localhost:8082'),
            'tesseract': ServiceEndpoint('tesseract', 'http://localhost:8081'),
            'research': ServiceEndpoint('research', 'http://localhost:8082'),
            'content': ServiceEndpoint('content', 'http://localhost:8082'),
            'workflow': ServiceEndpoint('workflow', 'http://localhost:8081'),
            'backend': ServiceEndpoint('backend', 'http://localhost:8000'),
            'public_backend': ServiceEndpoint('public_backend', os.getenv('PUBLIC_SERVER_URL', 'http://localhost:8000'))
        }
        
        for service_name, default_endpoint in defaults.items():
            if service_name not in self.services:
                self.services[service_name] = default_endpoint
    
    def _get_health_path(self, service_name: str) -> str:
        """Get appropriate health check path for service"""
        health_paths = {
            'langgraph': '/health',
            'tesseract': '/',
            'research': '/health',
            'content': '/health',
            'workflow': '/',
            'backend': '/health',
            'public_backend': '/health'
        }
        return health_paths.get(service_name, '/health')
    
    def get_service_url(self, service_name: str, endpoint: str = "") -> str:
        """
        Get the full URL for a service endpoint
        
        Args:
            service_name: Name of the service (e.g., 'langgraph', 'tesseract')
            endpoint: Specific endpoint path (e.g., '/research', '/workflow')
        
        Returns:
            Full URL for the service endpoint
        """
        if service_name not in self.services:
            raise ValueError(f"Service '{service_name}' not found in registry")
        
        base_url = self.services[service_name].base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        
        if endpoint:
            return f"{base_url}/{endpoint}"
        return base_url
    
    def resolve_tool_url(self, tool_config: Dict[str, Any]) -> str:
        """
        Resolve a tool's URL using service registry
        
        Supports multiple URL formats:
        - service://langgraph/research -> http://localhost:8082/research
        - ${LANGGRAPH_SERVICE_URL}/research -> resolved from env
        - http://localhost:8082/research -> used as-is
        """
        url = tool_config.get('url', '')
        
        # Handle service:// URLs
        if url.startswith('service://'):
            parts = url[10:].split('/', 1)  # Remove 'service://'
            service_name = parts[0]
            endpoint = f"/{parts[1]}" if len(parts) > 1 else ""
            return self.get_service_url(service_name, endpoint)
        
        # Handle ${VAR} substitution
        if '${' in url:
            import re
            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))
            
            url = re.sub(r'\$\{([^}]+)\}', replace_var, url)
        
        # Return URL as-is (including localhost URLs)
        return url
    
    async def health_check(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        if service_name not in self.services:
            return {"status": "unknown", "error": "Service not found"}
        
        service = self.services[service_name]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    service.health_url,
                    timeout=service.timeout
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return {
                            "status": "healthy",
                            "url": service.base_url,
                            "response": data
                        }
                    except:
                        return {
                            "status": "healthy",
                            "url": service.base_url,
                            "response": response.text
                        }
                else:
                    return {
                        "status": "unhealthy",
                        "url": service.base_url,
                        "error": f"HTTP {response.status_code}"
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "url": service.base_url,
                "error": str(e)
            }
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered services"""
        tasks = []
        service_names = []
        
        for service_name in self.services.keys():
            tasks.append(self.health_check(service_name))
            service_names.append(service_name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for service_name, result in zip(service_names, results):
            if isinstance(result, Exception):
                health_status[service_name] = {
                    "status": "error",
                    "error": str(result)
                }
            else:
                health_status[service_name] = result
        
        return health_status
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get information about the current deployment"""
        localhost_services = []
        external_services = []
        
        for service_name, service in self.services.items():
            if service.is_localhost():
                localhost_services.append(service_name)
            else:
                external_services.append(service_name)
        
        return {
            "deployment_type": "localhost" if len(localhost_services) > len(external_services) else "distributed",
            "localhost_services": localhost_services,
            "external_services": external_services,
            "total_services": len(self.services),
            "services": {name: service.base_url for name, service in self.services.items()}
        }
    
    def export_config_template(self) -> str:
        """Export a services.yaml template for companies to customize"""
        template = {
            "# Service Registry Configuration": None,
            "# Companies can customize these URLs for their deployment": None,
            "services": {
                "langgraph": {
                    "url": "https://your-langgraph-service.com",
                    "health_path": "/health",
                    "timeout": 10,
                    "required": True
                },
                "tesseract": {
                    "url": "https://your-tesseract-service.com", 
                    "health_path": "/",
                    "timeout": 10,
                    "required": True
                },
                "research": {
                    "url": "https://your-research-api.com",
                    "health_path": "/health",
                    "timeout": 15,
                    "required": False
                }
            },
            "# Environment Variables (alternative to services config)": None,
            "# LANGGRAPH_SERVICE_URL=https://your-langgraph.com": None,
            "# TESSERACT_SERVICE_URL=https://your-tesseract.com": None,
            "# RESEARCH_SERVICE_URL=https://your-research.com": None
        }
        
        # Clean up None values (comments)
        clean_template = {"services": template["services"]}
        
        return yaml.dump(clean_template, default_flow_style=False, sort_keys=False)

# Global service registry instance
service_registry = ServiceRegistry()

def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance"""
    return service_registry

def resolve_service_url(service_name: str, endpoint: str = "") -> str:
    """Convenience function to resolve service URLs"""
    return service_registry.get_service_url(service_name, endpoint) 