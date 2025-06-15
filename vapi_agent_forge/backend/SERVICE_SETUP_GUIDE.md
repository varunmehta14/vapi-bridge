# Dynamic Service Setup Guide

This system now uses **completely dynamic service routing** with no hardcoded tool mappings. All tools are routed through user-configured services.

## How It Works

1. **YAML Configuration**: Tools are defined in YAML with their parameters
2. **Service Configuration**: Each tool requires a corresponding service configuration
3. **Dynamic Routing**: The system routes tool calls to the configured service URLs
4. **Response Handling**: Services return responses in their own format, system extracts relevant content

## Setting Up a Service

### Step 1: Configure the Service via API

```bash
# Configure job_analytics service for user ID 1
curl -X POST "http://localhost:8000/users/1/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "job_analytics_service",
    "service_url": "http://localhost:8082/jobs/analytics",
    "health_path": "/health",
    "timeout": 30,
    "required": true
  }'
```

### Step 2: YAML Tool Configuration

```yaml
tools:
  - name: "job_analytics"
    description: "Get job statistics and analytics"
    parameters:
      type: "object"
      properties:
        query_type:
          type: "string"
          enum: ["total_jobs", "success_rate", "analytics_summary"]
      required: ["query_type"]
    action:
      method: "POST"
      url: "https://your-webhook-url/webhook/tool-call"
      json_body:
        tool_name: "job_analytics"
        parameters:
          query_type: "{query_type}"
```

## Service Configuration Mapping

The system looks for services using this pattern:
- Tool name: `job_analytics`
- Service key: `job_analytics_service`

## Response Format

Services can return responses in any of these formats:

### Option 1: Standard Fields
```json
{
  "result": "Your response content here",
  "summary": "Alternative response field",
  "content": "Another alternative field"
}
```

### Option 2: Direct String
```json
"Your direct string response"
```

### Option 3: Any JSON
The system will extract the most relevant field or return the full JSON.

## Example Service Configurations

### Research Service
```bash
curl -X POST "http://localhost:8000/users/1/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "quick_research_service",
    "service_url": "http://localhost:8082/quick-research",
    "timeout": 30
  }'
```

### Content Generation Service
```bash
curl -X POST "http://localhost:8000/users/1/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "generate_content_service", 
    "service_url": "http://localhost:8082/generate-content",
    "timeout": 45
  }'
```

## Benefits of Dynamic Routing

1. **No Code Changes**: Add new tools without modifying the webhook handler
2. **Flexible Services**: Services can be on different hosts/ports
3. **User-Specific**: Each user can have different service configurations
4. **Easy Testing**: Swap service URLs for testing without code changes
5. **Service Independence**: Each service handles its own parameter mapping and response formatting

## Error Handling

If a service is not configured for a tool, the system returns:
```json
{
  "results": [{
    "toolCallId": "xxx",
    "error": "Service not configured for tool: tool_name"
  }]
}
```

## Migration from Static to Dynamic

1. Remove hardcoded tool mappings ✅
2. Configure services via API
3. Update YAML configurations to use webhook format
4. Test each tool individually
5. Services handle their own response formatting 