'use client'

import React from 'react'

interface ConfigTemplatesProps {
  onTemplateSelect: (template: string) => void
}

const ConfigTemplates: React.FC<ConfigTemplatesProps> = ({ onTemplateSelect }) => {
  
  const voiceOptimizedTemplate = `assistant:
  name: "Quick Voice Assistant"
  model:
    provider: "google"
    model: "gemini-1.5-flash"
    system_prompt_template: |
      You are a Quick Voice Assistant optimized for voice conversations. Your responses should be:
      
      **CONCISE & IMMEDIATE:**
      - Provide direct, actionable answers in 2-3 sentences
      - Focus on the most important information first
      - Avoid lengthy explanations during voice calls
      
      **VOICE-OPTIMIZED:**
      - Use conversational language that sounds natural when spoken
      - Break complex information into digestible chunks
      - Ask follow-up questions to clarify user needs
      
      **ADAPTIVE:**
      - Use available tools based on user requests
      - Provide immediate responses when possible
      - Keep interactions focused and purposeful
      
      Always prioritize speed and relevance during voice calls.

  voice:
    provider: "playht"
    voiceId: "jennifer-playht"
  
  firstMessage: "Hi! I'm your quick voice assistant. I can help you with various tasks using my available tools. What would you like to do?"

tools:
  - name: "quick_search"
    description: "Perform quick searches and get immediate answers"
    parameters:
      type: "object"
      properties:
        query:
          type: "string"
          description: "Search query or question"
        type:
          type: "string"
          description: "Type of search"
          enum: ["general", "specific", "quick"]
          default: "quick"
      required: ["query"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/quick-search"
      json_body:
        query: "{query}"
        type: "{type}"
      response_template: "Let me search that for you..."

  - name: "voice_action"
    description: "Execute voice-optimized actions"
    parameters:
      type: "object"
      properties:
        action:
          type: "string"
          description: "Action to perform"
        parameters:
          type: "object"
          description: "Action parameters"
      required: ["action"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/voice-action"
      json_body:
        action: "{action}"
        parameters: "{parameters}"
      response_template: "Executing your request..."`

  const comprehensiveTemplate = `assistant:
  name: "Advanced Voice Assistant"
  model:
    provider: "google"
    model: "gemini-1.5-flash"
    system_prompt_template: |
      You are an Advanced Voice Assistant with comprehensive capabilities. You can:
      
      **RESEARCH & ANALYSIS:**
      - Conduct thorough research using multiple sources
      - Analyze complex information and provide insights
      - Generate detailed reports and summaries
      
      **CONTENT CREATION:**
      - Create high-quality content in various formats
      - Adapt tone and style to specific audiences
      - Generate marketing copy, articles, and documentation
      
      **TASK AUTOMATION:**
      - Execute complex workflows and processes
      - Integrate with multiple systems and APIs
      - Provide detailed status updates and results
      
      **VOICE INTERACTION:**
      - Maintain natural conversation flow
      - Provide clear explanations of complex topics
      - Ask clarifying questions when needed
      
      Use your tools strategically based on user needs and provide comprehensive assistance.

  voice:
    provider: "playht"
    voiceId: "jennifer-playht"
  
  firstMessage: "Hello! I'm your advanced voice assistant with comprehensive capabilities. I can help with research, content creation, task automation, and much more. What would you like to accomplish today?"

tools:
  - name: "comprehensive_research"
    description: "Conduct comprehensive research on any topic"
    parameters:
      type: "object"
      properties:
        topic:
          type: "string"
          description: "Research topic or question"
        depth:
          type: "string"
          description: "Research depth"
          enum: ["basic", "detailed", "comprehensive"]
          default: "detailed"
        sources:
          type: "integer"
          description: "Number of sources to research"
          minimum: 1
          maximum: 10
          default: 5
      required: ["topic"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/research"
      json_body:
        topic: "{topic}"
        depth: "{depth}"
        sources: "{sources}"
      response_template: "I'm conducting comprehensive research on {topic}. This will take a moment..."

  - name: "content_generation"
    description: "Generate high-quality content"
    parameters:
      type: "object"
      properties:
        type:
          type: "string"
          description: "Content type"
          enum: ["article", "blog", "report", "summary", "marketing", "email", "script"]
        topic:
          type: "string"
          description: "Content topic"
        tone:
          type: "string"
          description: "Content tone"
          enum: ["professional", "casual", "academic", "creative", "persuasive", "friendly"]
          default: "professional"
        length:
          type: "string"
          description: "Content length"
          enum: ["short", "medium", "long"]
          default: "medium"
      required: ["type", "topic"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/generate-content"
      json_body:
        type: "{type}"
        topic: "{topic}"
        tone: "{tone}"
        length: "{length}"
      response_template: "Creating {type} content about {topic} with a {tone} tone..."

  - name: "workflow_automation"
    description: "Execute automated workflows and processes"
    parameters:
      type: "object"
      properties:
        workflow:
          type: "string"
          description: "Workflow name or type"
        parameters:
          type: "object"
          description: "Workflow parameters"
        priority:
          type: "string"
          description: "Execution priority"
          enum: ["low", "normal", "high", "urgent"]
          default: "normal"
      required: ["workflow"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/workflow"
      json_body:
        workflow: "{workflow}"
        parameters: "{parameters}"
        priority: "{priority}"
      response_template: "Initiating {workflow} workflow with {priority} priority..."`

  const customTemplate = `assistant:
  name: "Custom Voice Assistant"
  model:
    provider: "openai"
    model: "gpt-4o-mini"
    system_prompt_template: |
      You are a Custom Voice Assistant designed for specific use cases. Customize this prompt based on your needs:
      
      **YOUR ROLE:**
      - Define your assistant's primary purpose
      - Specify the domain expertise (e.g., customer service, technical support, sales)
      - Set the personality and communication style
      
      **CAPABILITIES:**
      - List the main functions your assistant can perform
      - Define how it should handle different types of requests
      - Specify any limitations or boundaries
      
      **VOICE INTERACTION:**
      - Keep responses conversational and natural
      - Adapt complexity based on user needs
      - Use tools effectively to provide value
      
      Customize this template for your specific use case and requirements.

  voice:
    provider: "playht"
    voiceId: "jennifer-playht"
  
  firstMessage: "Hello! I'm your custom voice assistant. I've been configured for your specific needs. How can I help you today?"

tools:
  - name: "custom_tool_1"
    description: "Replace with your first custom tool"
    parameters:
      type: "object"
      properties:
        input:
          type: "string"
          description: "Tool input parameter"
        options:
          type: "object"
          description: "Additional options"
      required: ["input"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/tool1"
      json_body:
        input: "{input}"
        options: "{options}"
      response_template: "Processing your request with custom tool 1..."

  - name: "custom_tool_2"
    description: "Replace with your second custom tool"
    parameters:
      type: "object"
      properties:
        data:
          type: "string"
          description: "Data to process"
        format:
          type: "string"
          description: "Output format"
          enum: ["json", "text", "xml"]
          default: "json"
      required: ["data"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/tool2"
      json_body:
        data: "{data}"
        format: "{format}"
      response_template: "Processing your data with custom tool 2..."

  # Add more custom tools as needed
  - name: "custom_tool_3"
    description: "Add additional tools based on your requirements"
    parameters:
      type: "object"
      properties:
        query:
          type: "string"
          description: "Query or request"
      required: ["query"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/tool3"
      json_body:
        query: "{query}"
      response_template: "Executing custom tool 3..."`

  const templates = [
    {
      id: 'voice-optimized',
      name: '🎙️ Voice-Optimized Assistant',
      description: 'Fast, efficient responses optimized for voice interactions (2-5 seconds)',
      template: voiceOptimizedTemplate,
      features: ['Quick responses', 'Voice-optimized', 'Conversational', 'Immediate actions'],
      color: 'bg-green-600',
      useCase: 'Phone calls, voice commands, quick interactions'
    },
    {
      id: 'comprehensive',
      name: '🧠 Comprehensive Assistant',
      description: 'Advanced capabilities with research, content creation, and automation',
      template: comprehensiveTemplate,
      features: ['Research & analysis', 'Content generation', 'Workflow automation', 'Multi-tool integration'],
      color: 'bg-blue-600',
      useCase: 'Complex tasks, detailed research, content creation'
    },
    {
      id: 'custom',
      name: '⚙️ Custom Assistant Template',
      description: 'Fully customizable template for specific use cases and requirements',
      template: customTemplate,
      features: ['Fully customizable', 'Domain-specific', 'Custom tools', 'Flexible configuration'],
      color: 'bg-purple-600',
      useCase: 'Specialized domains, custom workflows, specific business needs'
    }
  ]

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-white mb-4">🚀 Voice Assistant Templates</h3>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className="bg-black/20 backdrop-blur-md rounded-lg p-4 border border-white/10 hover:border-white/30 transition-all"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">{template.name}</h4>
              <span className={`px-2 py-1 rounded text-xs text-white ${template.color}`}>
                Template
              </span>
            </div>
            
            <p className="text-sm text-gray-300 mb-3">{template.description}</p>
            
            <div className="mb-3">
              <h5 className="text-sm font-medium text-white mb-2">Features:</h5>
              <div className="flex flex-wrap gap-1">
                {template.features.map((feature, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-white/10 rounded text-xs text-gray-300"
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <h5 className="text-sm font-medium text-white mb-1">Best for:</h5>
              <p className="text-xs text-gray-400">{template.useCase}</p>
            </div>
            
            <button
              onClick={() => onTemplateSelect(template.template)}
              className={`w-full py-2 px-4 rounded-lg text-white font-medium transition-colors ${template.color} hover:opacity-90`}
            >
              Load Template
            </button>
          </div>
        ))}
      </div>
      
      <div className="mt-6 p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
        <h4 className="text-yellow-300 font-medium mb-2">💡 Dynamic Voice Agent System:</h4>
        <div className="text-yellow-200 text-sm space-y-1">
          <div>• <strong>Unlimited Agents:</strong> Create as many voice assistants as you need</div>
          <div>• <strong>Custom Tools:</strong> Add your own API endpoints and functionality</div>
          <div>• <strong>Voice Optimized:</strong> All templates are designed for natural voice interactions</div>
          <div>• <strong>Flexible Configuration:</strong> Adapt any template to your specific requirements</div>
          <div>• <strong>Real-time Detection:</strong> System automatically detects agent types and capabilities</div>
        </div>
        <div className="mt-3 text-xs text-yellow-300">
          🎯 <strong>Quick Start:</strong> Choose a template → Customize tools → Test configuration → Deploy your voice agent!
        </div>
      </div>
    </div>
  )
}

export default ConfigTemplates 