# Dynamic Voice Agent System Guide

## 🎯 **Overview**

The **Dynamic Voice Agent System** allows you to create unlimited voice assistants with custom capabilities, tools, and configurations. No more hardcoded agent names or limitations - build exactly what you need!

## 🚀 **Key Features**

### **Unlimited Voice Agents**
- Create as many voice assistants as you need
- Each agent can have unique capabilities and tools
- Dynamic detection of agent types and configurations
- Real-time configuration validation and testing

### **Custom Tool Integration**
- Add any API endpoints as tools
- Support for complex parameter schemas
- Flexible response handling and templates
- Voice-optimized tool configurations

### **Smart Agent Detection**
- Automatic detection of agent types (Research, Workflow, Custom)
- Real-time analysis of YAML configurations
- Dynamic status monitoring and health checks
- Intelligent service routing based on configuration

## 🛠️ **How to Create Voice Agents**

### **Step 1: Access the Agent Builder**
1. Navigate to `/agents` in your frontend
2. Click the **🤖 My Agents** tab to see your current agents
3. Click **🚀 Templates** to start with a template
4. Or click **📝 YAML Editor** to create from scratch

### **Step 2: Choose Your Agent Type**

#### **🎙️ Voice-Optimized Assistant**
- **Best for:** Phone calls, quick interactions
- **Response time:** 2-5 seconds
- **Features:** Immediate responses, conversational, cost-efficient
- **Use cases:** Customer service, quick queries, voice commands

#### **🧠 Comprehensive Assistant**
- **Best for:** Complex tasks, detailed work
- **Response time:** 30-60 seconds
- **Features:** Research, content generation, workflow automation
- **Use cases:** Research projects, content creation, business processes

#### **⚙️ Custom Assistant**
- **Best for:** Specialized domains
- **Response time:** Configurable
- **Features:** Fully customizable tools and behavior
- **Use cases:** Industry-specific needs, custom workflows

### **Step 3: Configure Your Agent**

#### **Basic Configuration**
```yaml
assistant:
  name: "Your Agent Name"
  model:
    provider: "openai"  # or "google"
    model: "gpt-4o-mini"  # or "gemini-1.5-flash"
    system_prompt_template: |
      Define your agent's personality and behavior here.
      Make it conversational for voice interactions.
  
  voice:
    provider: "playht"
    voiceId: "jennifer-playht"
  
  firstMessage: "Hello! How can I help you today?"
```

#### **Adding Custom Tools**
```yaml
tools:
  - name: "your_custom_tool"
    description: "What this tool does"
    parameters:
      type: "object"
      properties:
        input:
          type: "string"
          description: "Input parameter"
        options:
          type: "object"
          description: "Additional options"
      required: ["input"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api.com/endpoint"
      json_body:
        input: "{input}"
        options: "{options}"
      response_template: "Processing your request..."
```

### **Step 4: Test and Deploy**
1. Click **🧪 Test Config** to validate your configuration
2. Review the detected agent information
3. Click **Save Agent** to deploy
4. Monitor status in the dashboard

## 🔧 **Advanced Configuration**

### **Voice Optimization**
```yaml
# For cost-efficient voice calls
assistant:
  model:
    provider: "google"
    model: "gemini-1.5-flash"  # Faster, cheaper
  system_prompt_template: |
    Keep responses under 3 sentences for voice calls.
    Be direct and actionable.
    Ask follow-up questions if needed.
```

### **Multi-Tool Integration**
```yaml
tools:
  - name: "search_tool"
    # Search functionality
  - name: "analysis_tool"
    # Data analysis
  - name: "notification_tool"
    # Send notifications
  - name: "database_tool"
    # Database operations
```

### **Conditional Logic**
```yaml
system_prompt_template: |
  Based on the user's request:
  - Use search_tool for information queries
  - Use analysis_tool for data processing
  - Use notification_tool for alerts
  - Use database_tool for data storage/retrieval
```

## 📊 **Agent Management**

### **Dashboard Integration**
- **Dynamic Status Detection:** System automatically detects active agents
- **Real-time Monitoring:** Live status checks for each agent
- **Service Routing:** Intelligent routing based on configuration
- **Health Checks:** Automatic monitoring of agent endpoints

### **Agent Types Detection**
The system automatically detects:
- **Research Agents:** Tools like `research_topic`, `generate_content`
- **Workflow Agents:** Tools like `triggerFinancialAnalysisWorkflow`
- **Custom Agents:** Any other tool combinations

### **Status Monitoring**
Each agent shows:
- ✅ **Configuration Status:** Valid/Invalid YAML
- 🟢 **Service Status:** Online/Offline
- 🔧 **Tool Count:** Number of available tools
- 📊 **Performance:** Response times and success rates

## 🎯 **Best Practices**

### **Voice Optimization**
1. **Keep responses concise** (2-3 sentences for voice)
2. **Use conversational language** that sounds natural
3. **Provide immediate value** before detailed explanations
4. **Ask clarifying questions** to understand user needs
5. **Use voice-friendly formatting** (avoid complex lists)

### **Tool Design**
1. **Clear descriptions** for each tool
2. **Intuitive parameter names** and descriptions
3. **Proper error handling** in API endpoints
4. **Voice-optimized response templates**
5. **Reasonable timeout values** for voice calls

### **Configuration Management**
1. **Use templates** as starting points
2. **Test configurations** before deployment
3. **Monitor agent performance** regularly
4. **Update tools** based on user feedback
5. **Version control** your configurations

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Agent Not Detected**
- Check YAML syntax and indentation
- Verify tool names and URLs
- Ensure configuration is saved properly

#### **Tools Not Working**
- Verify API endpoints are accessible
- Check parameter schemas match your API
- Test endpoints independently first

#### **Voice Quality Issues**
- Adjust system prompt for conversational tone
- Optimize response templates for voice
- Test with actual voice calls

#### **Performance Problems**
- Use voice-optimized templates for speed
- Minimize tool complexity for quick responses
- Monitor response times in dashboard

### **Debug Steps**
1. **Test Configuration:** Use the built-in validator
2. **Check Logs:** Monitor console for errors
3. **Test Tools:** Verify API endpoints work
4. **Voice Test:** Try actual voice interactions
5. **Monitor Dashboard:** Check real-time status

## 🌟 **Example Configurations**

### **Customer Service Agent**
```yaml
assistant:
  name: "Customer Service Assistant"
  system_prompt_template: |
    You are a helpful customer service representative.
    Be friendly, professional, and solution-focused.
    Always try to resolve issues quickly.

tools:
  - name: "lookup_order"
    description: "Look up customer order information"
  - name: "process_refund"
    description: "Process refund requests"
  - name: "escalate_issue"
    description: "Escalate complex issues to human agents"
```

### **Sales Assistant**
```yaml
assistant:
  name: "Sales Assistant"
  system_prompt_template: |
    You are a knowledgeable sales assistant.
    Help customers find the right products.
    Be persuasive but not pushy.

tools:
  - name: "product_search"
    description: "Search product catalog"
  - name: "check_inventory"
    description: "Check product availability"
  - name: "calculate_pricing"
    description: "Calculate pricing and discounts"
```

### **Technical Support Agent**
```yaml
assistant:
  name: "Technical Support Assistant"
  system_prompt_template: |
    You are a technical support specialist.
    Provide clear, step-by-step solutions.
    Ask diagnostic questions when needed.

tools:
  - name: "run_diagnostics"
    description: "Run system diagnostics"
  - name: "access_knowledge_base"
    description: "Search technical documentation"
  - name: "create_ticket"
    description: "Create support tickets for complex issues"
```

## 🚀 **Getting Started Checklist**

- [ ] Access the Agent Builder at `/agents`
- [ ] Choose a template that matches your use case
- [ ] Customize the agent name and system prompt
- [ ] Add your custom tools and API endpoints
- [ ] Test the configuration using the validator
- [ ] Deploy and monitor your agent
- [ ] Test with actual voice interactions
- [ ] Iterate based on user feedback

## 💡 **Pro Tips**

1. **Start Simple:** Begin with basic tools and add complexity gradually
2. **Voice First:** Always design with voice interaction in mind
3. **Test Early:** Validate configurations before full deployment
4. **Monitor Performance:** Keep track of response times and success rates
5. **User Feedback:** Collect and act on user feedback regularly
6. **Version Control:** Keep track of configuration changes
7. **Documentation:** Document your custom tools and workflows

---

**The Dynamic Voice Agent System gives you unlimited flexibility to create exactly the voice assistants you need!** 🎉

Ready to build your first dynamic voice agent? Start with a template and customize it for your specific needs! 