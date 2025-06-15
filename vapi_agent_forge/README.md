# 🤖 Vapi Agent Forge - User Authentication & Voice Agent Management

A complete user authentication and voice agent management system built with FastAPI, Next.js, and Vapi.ai integration.

## ✨ Features

### 🔐 User Authentication
- **Simple Username-based Login** - No passwords required for development
- **User Management** - Create and manage multiple users
- **Session Persistence** - Login state maintained across browser sessions

### 🎤 Voice Agent Management
- **User-specific Voice Agents** - Each user can create and manage their own voice agents
- **YAML Configuration** - Define agents using simple YAML configurations
- **Template Library** - Quick-start templates for common use cases
- **Agent Types** - Auto-detection of Research, Workflow, and Custom agents
- **Real-time Creation** - Instantly create Vapi assistants from configurations

### 📊 Interaction Logging
- **Complete Audit Trail** - Log all voice interactions per user
- **Real-time Monitoring** - Track calls, messages, and function calls
- **User Analytics** - View interaction history and patterns

### 🛠️ System Management
- **Service Status Monitoring** - Real-time health checks
- **Configuration Validation** - YAML syntax and structure validation
- **Dynamic Assistant Creation** - Create assistants on-demand from current config

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd vapi_agent_forge/backend
pip install -r requirements.txt

# Create .env file with your API keys
echo "VAPI_API_KEY=your_vapi_api_key" > .env
echo "VAPI_PUBLIC_KEY=your_vapi_public_key" >> .env
echo "PUBLIC_SERVER_URL=http://localhost:8000" >> .env

# Start the backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd vapi_agent_forge/frontend
npm install
npm run dev
```

### 3. Access the Application
- **Login Page**: http://localhost:3000/login
- **Dashboard**: http://localhost:3000/ (redirects to login if not authenticated)
- **Voice Agents**: http://localhost:3000/voice-agents

## 📱 User Interface

### Login Page (`/login`)
- Enter a username to create/login to an account
- Select from existing users
- Automatic account creation for new usernames

### Dashboard (`/`)
- Service status monitoring
- YAML configuration editor
- Voice interface for testing
- Quick navigation to voice agents

### Voice Agents Page (`/voice-agents`)
- View all your voice agents
- Create new agents with templates
- Delete existing agents
- View interaction history

## 🎯 Creating Voice Agents

### Using Templates
1. Go to Voice Agents page
2. Click "Create Agent"
3. Choose a template:
   - **🔬 Research Assistant** - For research and content generation
   - **🎧 Customer Support** - For customer service interactions
4. Customize the YAML configuration
5. Click "Create Agent"

### Custom Configuration
Create your own YAML configuration:

```yaml
assistant:
  name: "My Custom Assistant"
  model:
    provider: "openai"
    model: "gpt-4"
    system_prompt_template: |
      You are a helpful assistant specialized in [your domain].
  voice:
    provider: "playht"
    voiceId: "jennifer"
  firstMessage: "Hello! How can I help you today?"

tools:
  - name: "my_tool"
    description: "Description of what this tool does"
    parameters:
      type: "object"
      properties:
        param1:
          type: "string"
          description: "Parameter description"
      required: ["param1"]
    action:
      method: "POST"
      url: "http://your-api.com/endpoint"
      json_body:
        input: "{param1}"
      response_format: "Result: {response.output}"
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/login` - Login/create user
- `GET /auth/users` - List all users

### Voice Agents
- `POST /users/{user_id}/voice-agents` - Create voice agent
- `GET /users/{user_id}/voice-agents` - Get user's voice agents
- `DELETE /users/{user_id}/voice-agents/{agent_id}` - Delete voice agent

### Interactions
- `POST /users/{user_id}/interactions` - Log interaction
- `GET /users/{user_id}/interactions` - Get interaction history

### System
- `GET /config/yaml` - Get current configuration
- `POST /config/validate` - Validate YAML configuration
- `GET /vapi/public-key` - Get Vapi public key

## 🗄️ Database Schema

The system uses SQLite with three main tables:

### Users
- `id` - Primary key
- `username` - Unique username
- `email` - Optional email
- `created_at` - Account creation timestamp

### Voice Agents
- `id` - Primary key
- `user_id` - Foreign key to users
- `name` - Agent name
- `vapi_assistant_id` - Vapi assistant ID
- `config_yaml` - YAML configuration
- `agent_type` - Auto-detected type (research/workflow/custom)
- `created_at` / `updated_at` - Timestamps

### Interactions
- `id` - Primary key
- `user_id` - Foreign key to users
- `voice_agent_id` - Foreign key to voice_agents
- `interaction_type` - Type of interaction
- `content` - Interaction content
- `timestamp` - When interaction occurred

## 🎤 Voice Interface

### Using Voice Agents
1. Select a voice agent from the dropdown
2. Click "Start Call" to begin conversation
3. Speak naturally - the AI will respond
4. Click "End Call" when finished

### Interaction Types Logged
- `call_started` - Voice call initiated
- `call_ended` - Voice call ended
- `user_message` - User speech transcript
- `function_call` - Tool/function executed
- `error` - Any errors that occurred
- `agent_created` - New agent created
- `agent_deleted` - Agent deleted

## 🔍 Monitoring & Debugging

### Service Status
The dashboard shows real-time status of:
- **LangGraph Research Assistant** (port 8082)
- **Vapi Agent Forge Backend** (port 8000)

### Logs
- Backend logs show detailed webhook interactions
- Frontend console shows Vapi events and errors
- Database interactions are logged for debugging

## 🛡️ Security Notes

- **Development Mode**: Uses simple username authentication
- **Production**: Implement proper authentication (OAuth, JWT, etc.)
- **API Keys**: Store in environment variables, never commit to code
- **Database**: SQLite for development, use PostgreSQL/MySQL for production

## 🚨 Troubleshooting

### Common Issues

1. **"Vapi not initialized"**
   - Check VAPI_PUBLIC_KEY in .env
   - Ensure backend is running on port 8000

2. **"No voice agents found"**
   - Create your first voice agent using templates
   - Check user is logged in properly

3. **"Failed to create voice agent"**
   - Validate YAML syntax
   - Check VAPI_API_KEY is correct
   - Ensure backend can reach external APIs

4. **Voice call fails**
   - Check microphone permissions
   - Ensure Vapi assistant was created successfully
   - Check browser console for errors

### Debug Mode
Enable detailed logging by setting environment variables:
```bash
export DEBUG=1
export LOG_LEVEL=DEBUG
```

## 🔄 Development Workflow

1. **Backend Changes**: Server auto-reloads with `--reload` flag
2. **Frontend Changes**: Next.js hot-reloads automatically
3. **Database Changes**: Delete `vapi_forge.db` to reset (development only)
4. **Configuration**: Update YAML templates in `sample_configs/`

## 📈 Future Enhancements

- [ ] Real user authentication (OAuth, JWT)
- [ ] Voice agent sharing between users
- [ ] Advanced analytics dashboard
- [ ] Voice agent versioning
- [ ] Bulk import/export of configurations
- [ ] Real-time collaboration
- [ ] Advanced permission system
- [ ] Integration with more LLM providers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Built with ❤️ using FastAPI, Next.js, TypeScript, and Vapi.ai** 