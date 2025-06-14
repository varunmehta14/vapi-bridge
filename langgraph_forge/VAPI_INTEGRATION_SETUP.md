# Vapi Integration Setup Guide

## 🌐 **HTTPS URLs (Required for Vapi)**

### **LangGraph Research Assistant**
- **HTTPS URL**: `https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app`
- **Local URL**: `http://localhost:8082`
- **Port**: 8082
- **Status**: ✅ Active

### **Existing Services**
- **Vapi Agent Forge**: `https://edec-2603-8000-baf0-4690-6112-2e68-bc0f-47a0.ngrok-free.app` (Port 8000)
- **Tesseract Engine**: (Port 8081 - add ngrok if needed)

## 🎯 **Vapi Configuration**

### **For Voice Calls (Cost-Optimized)**
Use `voice_optimized_config.yaml`:

```yaml
assistant:
  name: "Quick Research Assistant"
  model:
    provider: "google"
    model: "gemini-1.5-flash"

tools:
  - name: "research_topic"
    action:
      url: "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/quick-research"
  
  - name: "generate_content"
    action:
      url: "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/quick-content"
```

### **For Web Interface (Full Features)**
Use `sample_research_config.yaml`:

```yaml
tools:
  - name: "research_topic"
    action:
      url: "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/research"
  
  - name: "generate_content"
    action:
      url: "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/generate-content"
```

## 🔗 **Key Endpoints**

### **Voice-Optimized (Immediate Response)**
- **Quick Research**: `POST /quick-research` (2-5 seconds)
- **Quick Content**: `POST /quick-content` (3-8 seconds)
- **Vapi Webhook**: `POST /vapi-webhook` (immediate)

### **Full-Featured (Background Jobs)**
- **Research**: `POST /research` (30-60 seconds)
- **Content Generation**: `POST /generate-content` (20-40 seconds)
- **Job Status**: `GET /job-status/{job_id}`

### **Monitoring & Admin**
- **Health Check**: `GET /health`
- **Database Viewer**: `GET /admin/database`
- **Job List**: `GET /jobs`

## 🚀 **Setup Steps**

### **1. Start the Server**
```bash
cd langgraph_forge
source venv/bin/activate
python main.py
```

### **2. Start ngrok Tunnel**
```bash
ngrok http 8082 --region=us --name=langgraph
```

### **3. Get HTTPS URL**
```bash
curl -s http://localhost:4041/api/tunnels | grep public_url
```

### **4. Update Vapi Configuration**
- Use the HTTPS URL in your Vapi assistant configuration
- Choose voice-optimized config for cost efficiency
- Use full-featured config for comprehensive research

## 📊 **Performance Comparison**

| Configuration | Response Time | Cost | Best For |
|---------------|---------------|------|----------|
| Voice-Optimized | 2-5 seconds | LOW 💰 | Vapi voice calls |
| Full-Featured | 30-60 seconds | HIGH 💰💰💰 | Web interfaces |

## 🎙️ **Vapi Webhook Integration**

### **Function Call Format**
```json
{
  "message": {
    "type": "function-call",
    "functionCall": {
      "name": "research_topic",
      "parameters": {
        "query": "your research question"
      }
    }
  }
}
```

### **Response Format**
```json
{
  "result": "Here's what I found about [topic]: [immediate summary]"
}
```

## 🔧 **Testing Commands**

### **Test Health**
```bash
curl https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/health
```

### **Test Quick Research**
```bash
curl -X POST "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/quick-research" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence trends", "research_type": "quick"}'
```

### **Test Vapi Webhook**
```bash
curl -X POST "https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/vapi-webhook" \
  -H "Content-Type: application/json" \
  -d '{"message": {"type": "function-call", "functionCall": {"name": "research_topic", "parameters": {"query": "machine learning"}}}}'
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **ngrok URL Changes**
   - ngrok URLs change when restarted
   - Update configuration files with new URL
   - Use ngrok paid plan for static URLs

2. **CORS Issues**
   - Server has CORS enabled for all origins
   - Should work with Vapi without issues

3. **Timeout Issues**
   - Voice calls use quick endpoints (2-5 seconds)
   - Web interfaces can use background jobs
   - Check server logs for errors

### **Monitoring**
- **Database**: View at `/admin/database`
- **Jobs**: Check status at `/job-status/{job_id}`
- **Health**: Monitor at `/health`

## 🎉 **Ready for Vapi!**

Your LangGraph Research Assistant is now ready for Vapi integration with:
- ✅ HTTPS URL via ngrok
- ✅ Voice-optimized quick responses
- ✅ Cost-efficient processing
- ✅ Full-featured background jobs
- ✅ Comprehensive monitoring

**Use the voice-optimized config for Vapi calls to save ~27% on call costs!** 