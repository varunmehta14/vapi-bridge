# 🎯 VAPI API Key Integration Guide

## ✨ **New Feature: User-Specific VAPI API Keys**

Each company can now provide their own VAPI API key during signup, eliminating the need for global configuration!

## 🚀 **How It Works**

### **1. Company Signup with VAPI Key**

**Frontend**: Go to `http://localhost:3000/login` and click "Sign Up"

**Required Fields**:
- Company Username (e.g., "researchers")
- VAPI API Key (from your Vapi Dashboard)

**Optional Fields**:
- Email
- VAPI Public Key (for web calls)

**API Example**:
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researchers",
    "email": "team@researchers.com",
    "vapi_api_key": "your_vapi_api_key_here",
    "vapi_public_key": "your_vapi_public_key_here"
  }'
```

### **2. Voice Agent Creation**

Once signed up with a VAPI key, you can create voice agents:

```bash
# This will now work because user has VAPI key configured
curl -X POST http://localhost:8000/users/2/voice-agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LangGraph Research Assistant",
    "config_yaml": "name: Research Assistant\nmodel:\n  provider: openai\n  model: gpt-4\nvoice:\n  provider: 11labs\n  voiceId: 21m00Tcm4TlvDq8ikWAM\nfirstMessage: Hello! I am your research assistant.\ntools:\n  - name: research_query\n    description: Execute research using LangGraph Forge\n    url: service://langgraph_forge/research\n    method: POST\n    body:\n      query: \"{{query}}\"\n    parameters:\n      - name: query\n        type: string\n        required: true\nsystemMessage: You are a helpful research assistant.",
    "agent_type": "research"
  }'
```

### **3. VAPI Key Management**

**Check VAPI Configuration**:
```bash
curl http://localhost:8000/users/2/vapi-config
```

**Update VAPI Keys**:
```bash
curl -X POST http://localhost:8000/users/2/vapi-config \
  -H "Content-Type: application/json" \
  -d '{
    "vapi_api_key": "new_api_key",
    "vapi_public_key": "new_public_key"
  }'
```

## 🎯 **Complete LangGraph Forge Setup**

### **Step 1: Sign Up with VAPI Key**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researchers",
    "email": "team@researchers.com",
    "vapi_api_key": "YOUR_ACTUAL_VAPI_KEY"
  }'
```

### **Step 2: Configure LangGraph Service**
```bash
curl -X POST http://localhost:8000/users/USER_ID/services \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "langgraph_forge",
    "service_url": "http://localhost:8082",
    "health_path": "/health",
    "timeout": 15,
    "required": true
  }'
```

### **Step 3: Create Voice Agent**
Use the `langgraph_research_assistant.yaml` file:

```bash
curl -X POST http://localhost:8000/users/USER_ID/voice-agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LangGraph Research Assistant",
    "config_yaml": "'"$(cat langgraph_research_assistant.yaml | sed 's/"/\\"/g' | tr '\n' ' ')"'",
    "agent_type": "research"
  }'
```

## 🔧 **Frontend Features**

### **Login Page (`/login`)**
- **Sign Up Tab**: Create new account with VAPI key
- **Sign In Tab**: Login existing users
- **VAPI Key Update**: Update keys for existing users
- **User List**: Shows VAPI configuration status

### **User Status Indicators**
- ✅ **VAPI ✓**: User has configured VAPI API key
- ⚠️ **No VAPI**: User needs to add VAPI API key

## 🎙️ **Voice Agent YAML Format**

Your `langgraph_research_assistant.yaml` works perfectly:

```yaml
name: "LangGraph Research Assistant"
model:
  provider: openai
  model: gpt-4
  temperature: 0.7
voice:
  provider: 11labs
  voiceId: "21m00Tcm4TlvDq8ikWAM"
firstMessage: "Hello! I'm your LangGraph research assistant..."
tools:
  - name: "research_query"
    url: "service://langgraph_forge/research"  # Auto-resolves to localhost:8082
    method: "POST"
    # ... rest of tool config
systemMessage: |
  You are a research assistant powered by LangGraph Forge...
```

## 🔄 **URL Resolution**

The `service://` URLs automatically resolve using your configured services:

- `service://langgraph_forge/research` → `http://localhost:8082/research`
- `service://langgraph_forge/analyze` → `http://localhost:8082/analyze`

When you deploy with ngrok, just update the service URL - no YAML changes needed!

## 🚨 **Error Handling**

**No VAPI Key Error**:
```json
{
  "detail": "User has not configured VAPI API key. Please add your VAPI API key in settings."
}
```

**Solution**: Add VAPI key via signup or update existing user.

## 🎯 **Benefits**

1. **Multi-tenant**: Each company uses their own VAPI account
2. **No Global Config**: No need to set environment variables
3. **Flexible**: Users can update their keys anytime
4. **Secure**: Keys are stored per-user in database
5. **SaaS Ready**: Perfect for subscription-based business model

## 🚀 **Next Steps**

1. **Get VAPI API Key**: Visit [Vapi Dashboard](https://dashboard.vapi.ai)
2. **Sign Up**: Use the new signup form at `/login`
3. **Configure Services**: Add your LangGraph Forge service
4. **Create Voice Agents**: Use your YAML configuration
5. **Start Talking**: Your voice agents will use your VAPI account!

Your LangGraph Forge integration is now ready with user-specific VAPI keys! 🎉 