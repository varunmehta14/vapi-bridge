# 🚀 Tesseract Workflow Engine + Vapi Agent Forge

A complete end-to-end system that combines a robust workflow engine with intelligent voice interaction capabilities through Vapi's AI platform.

**🐍 Built for Python 3.11+ with Virtual Environment Support**

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│                 │    │                  │    │                    │
│   Vapi Cloud    │◄──►│  Vapi Agent      │◄──►│  Tesseract Engine  │
│   (Voice AI)    │    │  Forge (Port     │    │  (Port 8081)       │
│                 │    │  8000 + ngrok)   │    │                    │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         │                        │                        ▼
    Voice Calls              Tool Execution         ┌─────────────┐
         │                        │                 │  SQLite DB  │
         ▼                        │                 │  (Jobs &    │
   ┌──────────────┐              │                 │  Workflows) │
   │   Users      │              │                 └─────────────┘
   │   (Phone/    │              │
   │   Web Call)  │              ▼
   └──────────────┘        ┌──────────────────┐
                           │  Control Panel   │
                           │  (Frontend)      │
                           └──────────────────┘
```

## 🎯 Core Features

### **Tesseract Workflow Engine**
- **Database-driven workflows** with SQLAlchemy + SQLite
- **Two distinct API endpoints** for different interaction patterns
- **Background job processing** with FastAPI BackgroundTasks
- **Financial analysis workflows** with realistic simulation data
- **Comprehensive logging and error handling**

### **Vapi Agent Forge**
- **Dynamic tool configuration** via YAML
- **Intelligent request routing** between structured and unstructured queries
- **Response template system** for customized AI responses
- **Ngrok integration** for public webhook accessibility
- **Real-time tool testing interface**

## 🛠️ Quick Start (Recommended: Virtual Environments)

### Prerequisites

**Python 3.11+** is required. Install it if you haven't already:

```bash
# macOS (using Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev

# Windows
# Download from python.org or use winget:
winget install Python.Python.3.11
```

### 1️⃣ Automated Setup (Recommended)

```bash
# Clone the repository and navigate to it
git clone <your-repo-url>
cd vapi-bridge

# Run the automated setup script
python setup_venv.py
```

This script will:
- ✅ Check for Python 3.11+
- ✅ Create isolated virtual environments for both components
- ✅ Install all dependencies automatically
- ✅ Create convenient activation scripts

### 2️⃣ Start the System

**Option A: Use the startup script (handles virtual environments automatically)**
```bash
python start_system.py
```

**Option B: Use activation scripts**
```bash
# Unix/Linux/macOS
./activate_venvs.sh

# Windows
activate_venvs.bat
```

**Option C: Manual activation (for development)**
```bash
# Terminal 1 - Tesseract Engine
source tesseract_engine/venv/bin/activate
cd tesseract_engine && python main.py

# Terminal 2 - Vapi Agent Forge
source vapi_agent_forge/backend/venv/bin/activate
cd vapi_agent_forge/backend && python main.py
```

### 3️⃣ **Critical Step: Setup Ngrok**

> ⚠️ **This step is essential for Vapi integration!**

Vapi's cloud servers need to reach your local backend via secure HTTPS webhooks. Ngrok creates a secure tunnel:

```bash
# In a new terminal window
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123def.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** and set it as an environment variable:

```bash
export PUBLIC_SERVER_URL="https://abc123def.ngrok.io"
```

### 4️⃣ Configure Vapi Integration

```bash
# Set your Vapi API key
export VAPI_API_KEY="your_vapi_api_key_here"

# Activate the Vapi Forge virtual environment (if using venv)
source vapi_agent_forge/backend/venv/bin/activate

# Create a Vapi assistant
cd vapi_agent_forge/backend
python orchestrator.py
```

### 5️⃣ Access the Control Panel

Open your browser to:
```
vapi_agent_forge/frontend/index.html
```

The control panel provides:
- **System status monitoring**
- **Tool testing interface**
- **Setup validation**
- **Real-time debugging**

## 🔄 End-to-End Workflow Examples

### **Scenario A: Structured Financial Analysis**

```
1. User: "I need a financial analysis of Apple"
2. Vapi Agent: "What type of analysis would you like?"
3. User: "A standard review"
4. Vapi Agent: [Calls triggerFinancialAnalysisWorkflow]
5. Vapi Forge → Tesseract: POST /run_workflow/financial_analysis/user123
6. Tesseract: Creates job, returns {"job_id": "job_abc123"}
7. Vapi Agent: "Workflow initiated. The Job ID is job_abc123"
```

### **Scenario B: General Query Handling**

```
1. User: "Hey, can you check our compliance status?"
2. Vapi Agent: [Calls processGeneralRequest]
3. Vapi Forge → Tesseract: POST /receive_user_input/user123
4. Tesseract: Processes query, returns contextual response
5. Vapi Agent: [Speaks the intelligent response]
```

## 📁 Project Structure

```
├── tesseract_engine/          # Backend workflow engine
│   ├── venv/                 # Virtual environment (created by setup)
│   ├── main.py               # FastAPI server (port 8081)
│   ├── database.py           # SQLAlchemy models & DB management
│   ├── manager.py            # Workflow execution logic
│   └── requirements.txt      # Python dependencies
│
├── vapi_agent_forge/         # Vapi integration system
│   ├── backend/
│   │   ├── venv/            # Virtual environment (created by setup)
│   │   ├── main.py          # FastAPI server (port 8000)
│   │   ├── config.yaml      # Tool definitions & AI configuration
│   │   ├── orchestrator.py  # Vapi assistant management
│   │   └── requirements.txt # Python dependencies
│   └── frontend/
│       └── index.html       # Control panel interface
│
├── setup_venv.py            # Virtual environment setup script
├── start_system.py          # System startup script (venv-aware)
├── activate_venvs.sh        # Unix activation helper (created by setup)
├── activate_venvs.bat       # Windows activation helper (created by setup)
└── README.md               # This file
```

## 🧪 Testing the System

### Manual API Testing

**Test the Tesseract Engine directly:**
```bash
# Trigger financial analysis workflow
curl -X POST "http://localhost:8081/run_workflow/financial_analysis/test123" \
  -H "Content-Type: application/json" \
  -d '{"input_params": {"company_name": "Tesla", "analysis_type": "standard_review"}}'

# Send general query
curl -X POST "http://localhost:8081/receive_user_input/test123" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello there!"}'
```

**Test the Vapi Forge tools:**
```bash
# Test financial analysis tool
curl -X POST "http://localhost:8000/test-tool/triggerFinancialAnalysisWorkflow" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "company_name": "Apple", "analysis_type": "credit_risk"}'

# Test general request tool  
curl -X POST "http://localhost:8000/test-tool/processGeneralRequest" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "user_input": "What can you help me with?"}'
```

### Using the Control Panel

1. Open `vapi_agent_forge/frontend/index.html`
2. Check system status (all should be green)
3. Test individual tools with the interactive forms
4. Monitor responses in real-time

## 🔧 Configuration

### Environment Variables

```bash
# Required for Vapi integration
export VAPI_API_KEY="your_vapi_api_key"
export PUBLIC_SERVER_URL="https://your-ngrok-url.ngrok.io"

# Optional database configuration
export DATABASE_URL="sqlite:///tesseract.db"
```

### Tool Configuration (`config.yaml`)

The system's behavior is driven by the YAML configuration file:

```yaml
assistant:
  name: "Tesseract Command Assistant"
  model:
    provider: "openai"
    model: "gpt-4o-mini"
    system_prompt_template: "You are a specialized AI assistant..."
  
tools:
  - name: "triggerFinancialAnalysisWorkflow"
    description: "Run financial analysis on companies"
    # ... detailed configuration
  
  - name: "processGeneralRequest"
    description: "Handle general queries and commands"
    # ... detailed configuration
```

## 🚨 Troubleshooting

### Common Issues

**1. Python version issues**
- ✅ Ensure Python 3.11+ is installed: `python --version`
- ✅ Run `python setup_venv.py` to create proper virtual environments
- ✅ Use `python start_system.py` which detects virtual environments automatically

**2. Vapi webhooks failing**
- ✅ Ensure ngrok is running and PUBLIC_SERVER_URL is set
- ✅ Check that the Vapi Forge is accessible at the public URL
- ✅ Verify HTTPS (not HTTP) in the ngrok URL

**3. Virtual environment issues**
- ✅ Run `python setup_venv.py` to recreate environments
- ✅ Check that venv directories exist in both components
- ✅ Use activation scripts or `python start_system.py`

**4. Database connection errors**
- ✅ Ensure the tesseract_engine directory is writable
- ✅ Check that SQLite dependencies are installed in the virtual environment
- ✅ Try deleting `tesseract.db` and restarting

**5. Tool execution failures**
- ✅ Verify Tesseract Engine is running on port 8081
- ✅ Check tool parameters match the config.yaml schema
- ✅ Review logs in both services for error details

### Debug Mode

Enable detailed logging:

```bash
# Start services with debug logging
LOG_LEVEL=debug python main.py
```

### Virtual Environment Management

**Recreate virtual environments:**
```bash
python setup_venv.py
```

**Check virtual environment status:**
```bash
python start_system.py  # Will show venv status
```

**Manual cleanup:**
```bash
rm -rf tesseract_engine/venv
rm -rf vapi_agent_forge/backend/venv
python setup_venv.py
```

## 🎯 Next Steps

This system provides a solid foundation that you can extend:

1. **Add more workflows** to the Tesseract Engine
2. **Create additional tools** in `config.yaml`
3. **Implement authentication** for production use
4. **Add monitoring and analytics**
5. **Deploy to cloud infrastructure**

## 📞 Support

The system is designed to be self-contained and well-documented. Use the control panel for real-time debugging and testing. Each component logs detailed information to help diagnose issues.

### Quick Setup Summary

```bash
# 1. Install Python 3.11+
# 2. Setup virtual environments
python setup_venv.py

# 3. Start the system
python start_system.py

# 4. In another terminal, setup ngrok
ngrok http 8000
export PUBLIC_SERVER_URL="https://your-ngrok-url.ngrok.io"
export VAPI_API_KEY="your_api_key"

# 5. Create Vapi assistant
source vapi_agent_forge/backend/venv/bin/activate
cd vapi_agent_forge/backend && python orchestrator.py

# 6. Open the control panel
open vapi_agent_forge/frontend/index.html
```

---

**Built with ❤️ using Python 3.11+, FastAPI, SQLAlchemy, Vapi, and modern development practices.** 