# 🏢 Enterprise Deployment Guide

## Overview

The Vapi Agent Forge system has been redesigned to be **deployment-agnostic** and **enterprise-ready**. Companies can now deploy their own services and configure the system to work with any URL structure, moving away from hardcoded localhost dependencies.

## 🎯 Key Features

### ✅ **Flexible Service Discovery**
- **Environment Variables**: Configure service URLs via environment variables
- **Configuration Files**: Use `services.yaml` for complex deployments
- **Service URLs**: Support for `service://` URLs for automatic resolution
- **Variable Substitution**: Use `${VAR}` syntax for dynamic URL resolution

### ✅ **Multiple Deployment Patterns**
- **Local Development**: Default localhost behavior (no configuration needed)
- **Docker Compose**: Container-to-container communication
- **Kubernetes**: Service discovery within clusters
- **Cloud Deployment**: External HTTPS endpoints
- **Hybrid**: Mix of local and external services

### ✅ **Health Monitoring**
- Real-time service health checks
- Deployment type detection
- Service status dashboard
- Automatic failover capabilities

## 🚀 Quick Start

### 1. **Environment Variables (Recommended)**

Set environment variables for your service URLs:

```bash
# Research and Content Services
export LANGGRAPH_SERVICE_URL="https://research-api.yourcompany.com"
export CONTENT_SERVICE_URL="https://content-gen.yourcompany.com"

# Workflow Services  
export TESSERACT_SERVICE_URL="https://workflow-api.yourcompany.com"
export WORKFLOW_SERVICE_URL="https://automation.yourcompany.com"

# Backend Services
export PUBLIC_SERVER_URL="https://vapi-backend.yourcompany.com"
export BACKEND_SERVICE_URL="http://localhost:8000"  # Usually localhost

# Optional: Vapi Integration
export VAPI_API_KEY="your_vapi_api_key"
```

### 2. **Configuration File (Advanced)**

Create a `services.yaml` file in your backend directory:

```yaml
services:
  research:
    url: "https://research-api.yourcompany.com"
    health_path: "/health"
    timeout: 15
    required: true
  
  workflow:
    url: "https://workflow-engine.yourcompany.com"
    health_path: "/status"
    timeout: 10
    required: true
  
  content:
    url: "https://content-gen.yourcompany.com"
    health_path: "/health"
    timeout: 20
    required: false
```

### 3. **YAML Configuration**

Use the new URL formats in your agent configurations:

```yaml
assistant:
  name: "Enterprise Assistant"
  # ... assistant config ...

tools:
  # Service discovery URL
  - name: "research_topic"
    action:
      url: "service://research/analyze"
  
  # Environment variable substitution
  - name: "generate_content"
    action:
      url: "${CONTENT_SERVICE_URL}/generate"
  
  # Direct URL (works as before)
  - name: "external_api"
    action:
      url: "https://api.external-service.com/endpoint"
```

## 🏗️ Deployment Scenarios

### **Scenario 1: Local Development**
```bash
# No configuration needed - uses localhost defaults
npm run dev
```

### **Scenario 2: Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    environment:
      - LANGGRAPH_SERVICE_URL=http://research-service:8082
      - TESSERACT_SERVICE_URL=http://workflow-service:8081
  
  research-service:
    # Your research service container
  
  workflow-service:
    # Your workflow service container
```

### **Scenario 3: Kubernetes**
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vapi-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: LANGGRAPH_SERVICE_URL
          value: "http://research-service.default.svc.cluster.local:8082"
        - name: TESSERACT_SERVICE_URL
          value: "http://workflow-service.default.svc.cluster.local:8081"
```

### **Scenario 4: Cloud Deployment**
```bash
# Production environment variables
export LANGGRAPH_SERVICE_URL="https://research-api.company.com"
export TESSERACT_SERVICE_URL="https://workflow-api.company.com"
export PUBLIC_SERVER_URL="https://vapi-backend.company.com"
```

## 🔧 Configuration Priority

The system resolves service URLs in this order:

1. **Environment Variables** (highest priority)
2. **services.yaml file**
3. **Default localhost URLs** (fallback)

## 📊 Monitoring & Management

### **Service Status Dashboard**

Access the enhanced dashboard at `http://localhost:3000` to see:

- **Deployment Type**: Local vs Distributed
- **Service Health**: Real-time status of all services
- **URL Resolution**: See how URLs are being resolved
- **Configuration**: Current tool and assistant setup

### **API Endpoints**

New management endpoints:

```bash
# Get all services status
GET /services

# Get specific service status  
GET /services/{service_name}

# Get services configuration template
GET /services/config/template

# Reload service registry
POST /services/reload

# Get resolved configuration (for debugging)
GET /config/resolved
```

### **Health Checks**

Each service is automatically monitored:

```bash
# Check system status
curl http://localhost:8000/status

# Response includes:
{
  "services": {
    "langgraph": {"status": "healthy", "url": "https://..."},
    "tesseract": {"status": "healthy", "url": "https://..."}
  },
  "deployment": {
    "deployment_type": "distributed",
    "localhost_services": ["backend"],
    "external_services": ["langgraph", "tesseract"]
  }
}
```

## 🛠️ Migration Guide

### **From Localhost to Enterprise**

1. **Identify Current Services**
   ```bash
   # Check current configuration
   curl http://localhost:8000/config/resolved
   ```

2. **Set Environment Variables**
   ```bash
   export LANGGRAPH_SERVICE_URL="https://your-research-api.com"
   export TESSERACT_SERVICE_URL="https://your-workflow-api.com"
   ```

3. **Update YAML Configurations**
   ```yaml
   # Change from:
   url: "http://localhost:8082/research"
   
   # To:
   url: "service://research/analyze"
   # or
   url: "${LANGGRAPH_SERVICE_URL}/research"
   ```

4. **Restart and Verify**
   ```bash
   # Restart backend
   python -m uvicorn main:app --reload
   
   # Check deployment status
   curl http://localhost:8000/services
   ```

## 🔒 Security Considerations

### **Service Authentication**

Add authentication headers to service calls:

```yaml
# In your YAML configuration
tools:
  - name: "secure_api"
    action:
      url: "service://research/secure-endpoint"
      headers:
        Authorization: "Bearer ${API_TOKEN}"
        X-API-Key: "${RESEARCH_API_KEY}"
```

### **Network Security**

- Use HTTPS for all external service URLs
- Implement proper firewall rules
- Use VPNs or private networks for service communication
- Rotate API keys regularly

## 🚨 Troubleshooting

### **Common Issues**

1. **Service Not Found**
   ```
   Error: Service 'research' not found in registry
   ```
   **Solution**: Set `RESEARCH_SERVICE_URL` environment variable

2. **Connection Refused**
   ```
   Error: Connection refused to https://api.company.com
   ```
   **Solution**: Check service URL and network connectivity

3. **Health Check Failures**
   ```
   Status: unhealthy, Error: HTTP 404
   ```
   **Solution**: Verify health check endpoint path in services.yaml

### **Debug Commands**

```bash
# Check service registry
curl http://localhost:8000/services

# Get resolved URLs
curl http://localhost:8000/config/resolved

# Test specific service
curl http://localhost:8000/services/langgraph

# Reload configuration
curl -X POST http://localhost:8000/services/reload
```

## 📈 Best Practices

### **1. Service Naming**
- Use consistent service names across environments
- Follow naming conventions: `research`, `workflow`, `content`

### **2. Health Checks**
- Implement `/health` endpoints on all services
- Return JSON with status information
- Include version and build information

### **3. Configuration Management**
- Use environment variables for production
- Keep `services.yaml` for complex local development
- Document all required environment variables

### **4. Monitoring**
- Set up alerts for service health failures
- Monitor response times and error rates
- Log service discovery resolution

## 🎯 Example Configurations

### **Research Company**
```yaml
assistant:
  name: "Research Assistant"
  
tools:
  - name: "market_research"
    action:
      url: "service://research/market-analysis"
  
  - name: "competitor_analysis"
    action:
      url: "service://research/competitor-intel"
```

### **Financial Services**
```yaml
assistant:
  name: "Financial Advisor"
  
tools:
  - name: "portfolio_analysis"
    action:
      url: "service://workflow/financial-analysis"
  
  - name: "risk_assessment"
    action:
      url: "${RISK_API_URL}/assess"
```

### **Customer Support**
```yaml
assistant:
  name: "Support Agent"
  
tools:
  - name: "ticket_lookup"
    action:
      url: "https://support-api.company.com/tickets/{ticket_id}"
  
  - name: "knowledge_search"
    action:
      url: "service://content/knowledge-base"
```

## 🚀 Next Steps

1. **Deploy Your Services**: Set up your research, workflow, and content services
2. **Configure URLs**: Use environment variables or services.yaml
3. **Test Integration**: Use the dashboard to verify all services are healthy
4. **Create Agents**: Build voice agents using your custom services
5. **Monitor & Scale**: Use the built-in monitoring to optimize performance

---

**Need Help?** Check the service status dashboard at `http://localhost:3000` or use the API endpoints to debug configuration issues. 