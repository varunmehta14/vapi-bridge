# 🚀 Quick Setup Guide - Python 3.11 + Virtual Environments

This guide will get you up and running with the Tesseract + Vapi system using Python 3.11 and virtual environments.

## 📋 Prerequisites

- **Python 3.11+** installed
- **Git** for cloning repositories
- **Ngrok** for webhook tunneling (install from ngrok.com)

## ⚡ 5-Minute Setup

### Step 1: Install Python 3.11+

```bash
# macOS
brew install python@3.11

# Ubuntu/Debian  
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev

# Windows
winget install Python.Python.3.11
```

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd vapi-bridge

# Automated virtual environment setup
python setup_venv.py
```

### Step 3: Start the System

```bash
# Start both services automatically
python start_system.py
```

### Step 4: Setup Ngrok (New Terminal)

```bash
# Start ngrok tunnel
ngrok http 8000

# Copy the HTTPS URL and set environment variable
export PUBLIC_SERVER_URL="https://your-ngrok-url.ngrok.io"
export VAPI_API_KEY="your_vapi_api_key"
```

### Step 5: Create Vapi Assistant

```bash
# Activate virtual environment
source vapi_agent_forge/backend/venv/bin/activate

# Create assistant
cd vapi_agent_forge/backend
python orchestrator.py
```

### Step 6: Test Everything

- Open `vapi_agent_forge/frontend/index.html` in your browser
- Check that all status indicators are green
- Test the tools using the control panel

## 🔄 Alternative Activation Methods

### Using Activation Scripts

```bash
# Unix/Linux/macOS
./activate_venvs.sh

# Windows
activate_venvs.bat
```

### Manual Development Setup

```bash
# Terminal 1 - Tesseract Engine
source tesseract_engine/venv/bin/activate
cd tesseract_engine && python main.py

# Terminal 2 - Vapi Agent Forge  
source vapi_agent_forge/backend/venv/bin/activate
cd vapi_agent_forge/backend && python main.py
```

## 🆘 Quick Troubleshooting

### Python Version Issues
```bash
python --version  # Should show 3.11+
python setup_venv.py  # Recreate environments
```

### Virtual Environment Issues
```bash
# Clean slate
rm -rf tesseract_engine/venv vapi_agent_forge/backend/venv
python setup_venv.py
```

### Service Issues
```bash
# Check what's running on ports
lsof -i :8081  # Tesseract Engine
lsof -i :8000  # Vapi Agent Forge

# Kill processes if needed
kill -9 <PID>
```

### Ngrok Issues
```bash
# Make sure it's running
curl http://localhost:4040/api/tunnels

# Check environment variable
echo $PUBLIC_SERVER_URL
```

## 📞 Testing Commands

```bash
# Test Tesseract Engine
curl -X POST "http://localhost:8081/run_workflow/financial_analysis/test123" \
  -H "Content-Type: application/json" \
  -d '{"input_params": {"company_name": "Tesla", "analysis_type": "standard_review"}}'

# Test Vapi Forge
curl -X POST "http://localhost:8000/test-tool/triggerFinancialAnalysisWorkflow" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "company_name": "Apple", "analysis_type": "credit_risk"}'
```

## 💡 Pro Tips

1. **Always use virtual environments** - Run `python setup_venv.py` first
2. **Use the startup script** - `python start_system.py` handles everything
3. **Check the control panel** - Open `vapi_agent_forge/frontend/index.html` for status
4. **Keep ngrok running** - Vapi needs the public HTTPS URL
5. **Set environment variables** - Don't forget `PUBLIC_SERVER_URL` and `VAPI_API_KEY`

## 🎯 What You Get

- ✅ **Isolated Python 3.11 environments** for both components
- ✅ **Automatic dependency management** 
- ✅ **Production-ready architecture** with proper separation
- ✅ **Real-time testing interface** via control panel
- ✅ **Voice AI integration** with Vapi
- ✅ **Workflow engine** with financial analysis capabilities

---

**Need help?** Check the full README.md or use the control panel's testing interface! 