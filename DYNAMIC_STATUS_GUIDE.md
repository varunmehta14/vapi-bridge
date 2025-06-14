# Dynamic System Status Guide

## 🎯 **Overview**

The system now features **Dynamic Service Detection** that automatically detects which AI services are being used based on your YAML configuration and updates the system status display accordingly.

## 🔍 **How It Works**

### **Automatic Service Detection**
The dashboard analyzes your YAML configuration and detects:

1. **LangGraph Research Assistant** - Detected by:
   - `research_topic` or `generate_content` tools
   - `quick-research` or `quick-content` endpoints
   - Port `8082` references
   - `ngrok-free.app` URLs
   - "Research Assistant" in names
   - `gemini` model references

2. **Tesseract Engine** - Detected by:
   - `triggerFinancialAnalysisWorkflow` tool
   - `processGeneralRequest` tool
   - Port `8081` references
   - "Tesseract" in names
   - `financial_analysis` workflows

3. **Vapi Agent Forge** - Always shown as main backend (Port 8000)

### **Dynamic Status Display**
- ✅ **Active services** are highlighted with colored badges
- 🔍 **Port numbers** are automatically detected and displayed
- 📊 **Service descriptions** match the detected functionality
- 🔄 **Status checks** are performed on the correct ports

## 🚀 **Features**

### **Configuration-Based Detection**
```yaml
# This config will show LangGraph Research Assistant
tools:
  - name: "research_topic"
    action:
      url: "https://ngrok-url.ngrok-free.app/quick-research"
```

### **Multi-Service Support**
The system can detect and display multiple services simultaneously:
- LangGraph Research Assistant (Port 8082)
- Tesseract Engine (Port 8081)  
- Vapi Agent Forge (Port 8000)

### **Real-Time Updates**
- Status updates when configuration changes
- Automatic service detection on page refresh
- Live status checking for each detected service

## 📋 **Service Information Display**

Each detected service shows:
- **Service Name** and description
- **Port Number** (dynamically detected)
- **Status Badge** (🔬 Research, 🔧 Workflow, ⚙️ Backend)
- **Active Status** (✅ Active in Config / ⚪ Not in Config)
- **Connection Status** (🟢 Online / 🔴 Offline)
- **Status Messages** and error details

## 🎛️ **Control Panel Features**

### **Service Selection** (Agents Page)
1. Go to `/agents` page
2. Click **🔧 Service** tab
3. Select your target service
4. Templates and configurations will match your selection

### **Dynamic Dashboard** (Main Dashboard)
1. Configuration is automatically loaded
2. Services are detected from YAML
3. Status cards are generated dynamically
4. Each service gets appropriate status checks

## 🔧 **Configuration Examples**

### **LangGraph Configuration**
```yaml
assistant:
  name: "Research Assistant"
  model:
    provider: "google"
    model: "gemini-1.5-flash"

tools:
  - name: "research_topic"
    action:
      url: "https://your-ngrok.ngrok-free.app/quick-research"
```
**Result**: Shows LangGraph Research Assistant on port 8082

### **Tesseract Configuration**
```yaml
assistant:
  name: "Tesseract Command Assistant"

tools:
  - name: "triggerFinancialAnalysisWorkflow"
    action:
      url: "http://localhost:8081/run_workflow/financial_analysis/{user_id}"
```
**Result**: Shows Tesseract Engine on port 8081

### **Mixed Configuration**
```yaml
tools:
  - name: "research_topic"
    action:
      url: "https://ngrok.ngrok-free.app/research"
  - name: "triggerFinancialAnalysisWorkflow"
    action:
      url: "http://localhost:8081/run_workflow/financial_analysis/{user_id}"
```
**Result**: Shows both LangGraph (8082) and Tesseract (8081)

## 💡 **Benefits**

### **For Users**
- **Clear visibility** into which services are active
- **Accurate port information** without manual configuration
- **Relevant status checks** for your specific setup
- **Simplified troubleshooting** with service-specific information

### **For Developers**
- **Automatic service discovery** reduces configuration overhead
- **Flexible architecture** supports multiple AI services
- **Extensible detection** can be enhanced for new services
- **Consistent UI** regardless of backend configuration

## 🔄 **Status Updates**

The system automatically refreshes service status:
- **On page load** - Initial detection and status check
- **On configuration change** - Re-analyzes YAML and updates display
- **On manual refresh** - User-triggered status updates
- **On service selection** - Updates when switching services

## 🎯 **Use Cases**

1. **Development**: Quickly see which services are running
2. **Testing**: Verify correct service configuration
3. **Troubleshooting**: Identify offline or misconfigured services
4. **Monitoring**: Real-time status of your AI system components

## 🚨 **Troubleshooting**

### **Service Not Detected**
- Check YAML syntax and indentation
- Verify tool names and URLs match detection patterns
- Ensure configuration is saved and loaded properly

### **Wrong Port Displayed**
- Check URL patterns in your YAML configuration
- Verify service is running on the expected port
- Update detection patterns if using custom ports

### **Status Check Fails**
- Ensure service is actually running
- Check firewall and network connectivity
- Verify health check endpoints are available

---

**The dynamic system status makes your AI system more transparent, easier to manage, and simpler to troubleshoot!** 🎉 