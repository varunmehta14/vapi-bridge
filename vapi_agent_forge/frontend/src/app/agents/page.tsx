'use client'

import React, { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import Navigation from '../../components/Navigation'
import VoiceCall from '../../components/VoiceCall'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

interface User {
  id: number
  username: string
}

interface VoiceAgent {
  id: number
  name: string
  vapi_assistant_id: string
  agent_type: string
  created_at: string
  updated_at: string
}

interface Interaction {
  type: string
  content: string
  timestamp: string
  agent_name: string
}

interface DetectedAgentInfo {
  name: string
  type: 'research' | 'workflow' | 'custom' | 'unknown'
  description: string
  modelProvider: string
  voiceProvider: string
  toolCount: number
  hasSystemPrompt: boolean
  hasFirstMessage: boolean
  serverUrl?: string
}

export default function AgentsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [voiceAgents, setVoiceAgents] = useState<VoiceAgent[]>([])
  const [interactions, setInteractions] = useState<Interaction[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [yamlConfig, setYamlConfig] = useState(`# Dynamic Voice Agent Configuration
assistant:
  name: "Dynamic Voice Assistant"
  model:
    provider: "openai"
    model: "gpt-4o-mini"
    system_prompt_template: |
      You are an intelligent voice assistant. Adapt your responses based on the tools available to you.
      
      Guidelines:
      - Be conversational and natural in voice interactions
      - Use the appropriate tools based on user requests
      - Provide clear, concise responses optimized for voice
      - Ask clarifying questions when needed
      
  voice: 
    provider: "playht"
    voiceId: "jennifer-playht"
  
  firstMessage: "Hello! I'm your voice assistant. How can I help you today?"

tools:
  # Add your custom tools here
  - name: "example_tool"
    description: "Example tool - replace with your actual tools"
    parameters:
      type: "object"
      properties:
        query:
          type: "string"
          description: "User query or request"
      required: ["query"]
    action:
      type: "api_call"
      method: "POST"
      url: "https://your-api-endpoint.com/process"
      json_body:
        query: "{query}"
      response_template: "Processing your request..."
`)

  const [testResult, setTestResult] = useState<any>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [activeTab, setActiveTab] = useState<'agents' | 'templates' | 'editor' | 'test' | 'services' | 'voice-call'>('agents')
  const [selectedService, setSelectedService] = useState<{id: string, port: number, configPath: string}>({
    id: 'dynamic',
    port: 8000,
    configPath: '/config/yaml'
  })
  const [detectedAgent, setDetectedAgent] = useState<DetectedAgentInfo | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newAgent, setNewAgent] = useState({
    name: '',
    config_yaml: ''
  })

  // Add service configuration state
  const [userServices, setUserServices] = useState<any[]>([])
  const [showServiceForm, setShowServiceForm] = useState(false)
  const [newService, setNewService] = useState({
    service_name: '',
    service_url: '',
    health_path: '/health',
    timeout: 10,
    required: true
  })
  const [serviceTestResults, setServiceTestResults] = useState<Record<string, any>>({})
  const [isTestingService, setIsTestingService] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (!userData) {
      router.push('/login')
      return
    }
    
    const parsedUser = JSON.parse(userData)
    setUser(parsedUser)
    loadUserData(parsedUser.id)
    loadUserServices(parsedUser.id)
    
    // Update detected agent info on mount
    const agentInfo = detectAgentFromConfig(yamlConfig)
    setDetectedAgent(agentInfo)
  }, [router])

  const loadUserData = async (userId: number) => {
    setIsLoading(true)
    try {
      // Load voice agents
      const agentsResponse = await fetch(`http://localhost:8000/users/${userId}/voice-agents`)
      const agentsData = await agentsResponse.json()
      if (agentsData.status === 'success') {
        setVoiceAgents(agentsData.voice_agents)
      }

      // Load interactions
      const interactionsResponse = await fetch(`http://localhost:8000/users/${userId}/interactions`)
      const interactionsData = await interactionsResponse.json()
      if (interactionsData.status === 'success') {
        setInteractions(interactionsData.interactions)
      }
    } catch (error) {
      console.error('Failed to load user data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadUserServices = async (userId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/users/${userId}/services`)
      const data = await response.json()
      if (data.status === 'success') {
        setUserServices(data.services)
      }
    } catch (error) {
      console.error('Failed to load user services:', error)
    }
  }

  const detectAgentFromConfig = (yamlConfig: string): DetectedAgentInfo => {
    const lines = yamlConfig.split('\n')
    const info: Partial<DetectedAgentInfo> = {
      toolCount: 0,
      hasSystemPrompt: false,
      hasFirstMessage: false,
      modelProvider: 'unknown',
      voiceProvider: 'unknown'
    }

    // Extract information from YAML
    lines.forEach(line => {
      const trimmed = line.trim()
      
      if (trimmed.includes('name:') && !trimmed.startsWith('#')) {
        const value = trimmed.split('name:')[1]?.trim().replace(/["']/g, '')
        if (value) info.name = value
      }
      
      if (trimmed.includes('provider:') && !trimmed.startsWith('#')) {
        const value = trimmed.split('provider:')[1]?.trim().replace(/["']/g, '')
        if (value) {
          if (line.includes('voice')) {
            info.voiceProvider = value
          } else {
            info.modelProvider = value
          }
        }
      }
      
      if (trimmed.includes('system_prompt_template:') || trimmed.includes('systemMessage:')) {
        info.hasSystemPrompt = true
      }
      
      if (trimmed.includes('firstMessage:')) {
        info.hasFirstMessage = true
      }
      
      if (trimmed.includes('serverUrl:') || trimmed.includes('server_url:')) {
        const value = trimmed.split(/serverUrl:|server_url:/)[1]?.trim().replace(/["']/g, '')
        if (value) info.serverUrl = value
      }
    })

    // Count tools
    info.toolCount = (yamlConfig.match(/- name:/g) || []).length

    // Detect agent type based on tools and content
    let type: DetectedAgentInfo['type'] = 'unknown'
    let description = 'Custom voice assistant'

    if (yamlConfig.includes('research_topic') || yamlConfig.includes('generate_content')) {
      type = 'research'
      description = 'AI-powered research and content generation assistant'
    } else if (yamlConfig.includes('triggerFinancialAnalysisWorkflow') || yamlConfig.includes('financial_analysis')) {
      type = 'workflow'
      description = 'Workflow automation and business process assistant'
    } else if (info.toolCount > 0) {
      type = 'custom'
      description = `Custom assistant with ${info.toolCount} specialized tools`
    }

    return {
      name: info.name || 'Unnamed Assistant',
      type,
      description,
      modelProvider: info.modelProvider || 'unknown',
      voiceProvider: info.voiceProvider || 'unknown',
      toolCount: info.toolCount || 0,
      hasSystemPrompt: info.hasSystemPrompt || false,
      hasFirstMessage: info.hasFirstMessage || false,
      serverUrl: info.serverUrl
    }
  }

  const handleCreateAgent = async () => {
    if (!user || !newAgent.name.trim() || !newAgent.config_yaml.trim()) {
      alert('Please fill in all fields')
      return
    }

    setIsSaving(true)
    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/voice-agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newAgent.name,
          config_yaml: newAgent.config_yaml
        }),
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        setNewAgent({ name: '', config_yaml: '' })
        setShowCreateForm(false)
        setTestResult({
          success: true,
          message: 'Voice agent created successfully!',
          data: data
        })
        loadUserData(user.id) // Reload data
      } else {
        setTestResult({
          success: false,
          message: 'Failed to create voice agent: ' + (data.detail || 'Unknown error'),
          data: data
        })
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Network error occurred',
        data: { error: error instanceof Error ? error.message : 'Unknown error' }
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteAgent = async (agentId: number) => {
    if (!user || !confirm('Are you sure you want to delete this voice agent?')) {
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/voice-agents/${agentId}`, {
        method: 'DELETE',
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        setTestResult({
          success: true,
          message: 'Voice agent deleted successfully!',
          data: data
        })
        loadUserData(user.id) // Reload data
      } else {
        setTestResult({
          success: false,
          message: 'Failed to delete voice agent',
          data: data
        })
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Network error occurred',
        data: { error: error instanceof Error ? error.message : 'Unknown error' }
      })
    }
  }

  const handleTemplateSelect = (template: string) => {
    setYamlConfig(template)
    setNewAgent({ ...newAgent, config_yaml: template })
    setActiveTab('editor')
    setTestResult(null)
    // Update detected agent info
    const agentInfo = detectAgentFromConfig(template)
    setDetectedAgent(agentInfo)
  }

  const handleConfigChange = (value: string) => {
    setYamlConfig(value)
    setNewAgent({ ...newAgent, config_yaml: value })
    // Update detected agent info in real-time
    const agentInfo = detectAgentFromConfig(value)
    setDetectedAgent(agentInfo)
  }

  const handleSaveConfig = async () => {
    setIsSaving(true)
    try {
      const response = await fetch('http://localhost:8000/config/yaml', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml: yamlConfig })
      })
      
      const result = await response.json()
      setTestResult({
        success: response.ok,
        message: response.ok ? 'Configuration saved successfully!' : 'Failed to save configuration',
        data: result
      })
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Network error occurred',
        data: { error: error instanceof Error ? error.message : 'Unknown error' }
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleTest = async () => {
    setIsTesting(true)
    try {
      let response;
      let testEndpoint;
      
      if (selectedService.id === 'dynamic') {
        // For the main backend (port 8000), test the configuration by saving it first
        testEndpoint = 'Configuration Test';
        response = await fetch('http://localhost:8000/config/yaml', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ yaml: yamlConfig })
        });
        
        if (response.ok) {
          // If config save is successful, also test the health endpoint
          const healthResponse = await fetch('http://localhost:8000/health');
          const healthData = await healthResponse.json();
          
          setTestResult({
            success: true,
            message: 'Configuration test completed successfully! Backend is healthy.',
            data: {
              config_saved: true,
              health_check: healthData,
              test_type: 'configuration_validation'
            }
          });
        } else {
          const errorData = await response.json();
          setTestResult({
            success: false,
            message: 'Configuration test failed - invalid YAML or backend error',
            data: errorData
          });
        }
      } else if (selectedService.id === 'research') {
        // For research service (port 8082), test the health endpoint
        testEndpoint = 'Research Service Health Check';
        response = await fetch('http://localhost:8082/health');
        
        if (response.ok) {
          const data = await response.json();
          setTestResult({
            success: true,
            message: 'Research service is healthy and responding!',
            data: {
              ...data,
              test_type: 'health_check',
              service: 'research'
            }
          });
        } else {
          setTestResult({
            success: false,
            message: 'Research service health check failed',
            data: { 
              status: response.status,
              test_type: 'health_check',
              service: 'research'
            }
          });
        }
      } else if (selectedService.id === 'workflow') {
        // For workflow service (port 8083), test the health endpoint
        testEndpoint = 'Workflow Service Health Check';
        response = await fetch('http://localhost:8083/health');
        
        if (response.ok) {
          const data = await response.json();
          setTestResult({
            success: true,
            message: 'Workflow service is healthy and responding!',
            data: {
              ...data,
              test_type: 'health_check',
              service: 'workflow'
            }
          });
        } else {
          setTestResult({
            success: false,
            message: 'Workflow service health check failed',
            data: { 
              status: response.status,
              test_type: 'health_check',
              service: 'workflow'
            }
          });
        }
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: `Test failed - ${selectedService.id} service unavailable`,
        data: { 
          error: error instanceof Error ? error.message : 'Unknown error',
          service: selectedService.id,
          test_type: 'connection_error'
        }
      })
    } finally {
      setIsTesting(false)
    }
  }

  const getAgentTypeIcon = (type: string) => {
    switch (type) {
      case 'research': return '🔬'
      case 'workflow': return '🔧'
      case 'custom': return '⚙️'
      default: return '🤖'
    }
  }

  const getAgentTypeColor = (type: string) => {
    switch (type) {
      case 'research': return 'bg-green-600'
      case 'workflow': return 'bg-blue-600'
      case 'custom': return 'bg-purple-600'
      default: return 'bg-gray-600'
    }
  }

  const templates = {
    research: `assistant:
  name: "Research Assistant"
  model:
    provider: "openai"
    model: "gpt-4"
    system_prompt_template: |
      You are a helpful research assistant. You can help users research topics, find information, and generate content.
      When users ask for research, use the available tools to gather information and provide comprehensive answers.
  voice:
    provider: "playht"
    voiceId: "jennifer"
  firstMessage: "Hi! I'm your research assistant. I can help you research any topic or generate content. What would you like to explore today?"

tools:
  - name: "research_topic"
    description: "Research a specific topic and provide comprehensive information"
    parameters:
      type: "object"
      properties:
        topic:
          type: "string"
          description: "The topic to research"
        depth:
          type: "string"
          enum: ["basic", "detailed", "comprehensive"]
          description: "How detailed the research should be"
      required: ["topic"]
    action:
      method: "POST"
      url: "http://localhost:8082/research"
      json_body:
        topic: "{topic}"
        depth: "{depth}"
      response_format: "Research completed for {topic}: {response.summary}"`,

    workflow: `assistant:
  name: "Workflow Assistant"
  model:
    provider: "openai"
    model: "gpt-4"
    system_prompt_template: |
      You are a workflow automation assistant. You can help users trigger and manage business processes.
      Use the available tools to execute workflows and provide status updates.
  voice:
    provider: "playht"
    voiceId: "jennifer"
  firstMessage: "Hello! I'm your workflow assistant. I can help you automate business processes. What workflow would you like to run?"

tools:
  - name: "trigger_workflow"
    description: "Trigger a business workflow"
    parameters:
      type: "object"
      properties:
        workflow_name:
          type: "string"
          description: "Name of the workflow to trigger"
        parameters:
          type: "object"
          description: "Workflow parameters"
      required: ["workflow_name"]
    action:
      method: "POST"
      url: "http://localhost:8083/workflow/trigger"
      json_body:
        workflow: "{workflow_name}"
        params: "{parameters}"
      response_format: "Workflow {workflow_name} triggered: {response.status}"`,

    support: `assistant:
  name: "Customer Support Assistant"
  model:
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt_template: |
      You are a friendly and helpful customer support assistant. Your goal is to help customers with their questions,
      resolve issues, and provide excellent service. Always be polite, empathetic, and solution-oriented.
  voice:
    provider: "playht"
    voiceId: "jennifer"
  firstMessage: "Hello! I'm here to help you with any questions or issues you might have. How can I assist you today?"

tools:
  - name: "search_knowledge_base"
    description: "Search the knowledge base for answers to common questions"
    parameters:
      type: "object"
      properties:
        query:
          type: "string"
          description: "Search query for the knowledge base"
      required: ["query"]
    action:
      method: "GET"
      url: "http://localhost:8000/kb/search?q={query}"
      response_format: "Found answer: {response.answer}"`
  }

  const handleAddService = async () => {
    if (!user || !newService.service_name || !newService.service_url) {
      alert('Please fill in service name and URL')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/services`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newService),
      })

      const data = await response.json()
      if (data.status === 'success') {
        await loadUserServices(user.id)
        setNewService({
          service_name: '',
          service_url: '',
          health_path: '/health',
          timeout: 10,
          required: true
        })
        setShowServiceForm(false)
      } else {
        alert('Failed to add service: ' + data.message)
      }
    } catch (error) {
      console.error('Failed to add service:', error)
      alert('Failed to add service')
    }
  }

  const handleDeleteService = async (serviceName: string) => {
    if (!user) return

    if (confirm(`Are you sure you want to delete the service "${serviceName}"?`)) {
      try {
        const response = await fetch(`http://localhost:8000/users/${user.id}/services/${serviceName}`, {
          method: 'DELETE',
        })

        const data = await response.json()
        if (data.status === 'success') {
          await loadUserServices(user.id)
        } else {
          alert('Failed to delete service: ' + data.message)
        }
      } catch (error) {
        console.error('Failed to delete service:', error)
        alert('Failed to delete service')
      }
    }
  }

  const handleTestService = async (serviceName: string) => {
    if (!user) return

    setIsTestingService({ ...isTestingService, [serviceName]: true })

    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/services/${serviceName}/test`, {
        method: 'POST',
      })

      const data = await response.json()
      setServiceTestResults({ ...serviceTestResults, [serviceName]: data })
    } catch (error) {
      console.error('Failed to test service:', error)
      setServiceTestResults({ 
        ...serviceTestResults, 
        [serviceName]: { 
          status: 'error', 
          error: 'Failed to test service',
          message: 'Network error or service unavailable'
        } 
      })
    } finally {
      setIsTestingService({ ...isTestingService, [serviceName]: false })
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading agents...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <Navigation currentPage="agents" user={user} />

        {/* Agent Detection Card */}
        {detectedAgent && activeTab === 'editor' && (
          <div className="mb-8 bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
            <div className="flex items-center gap-4 mb-4">
              <span className="text-4xl">{getAgentTypeIcon(detectedAgent.type)}</span>
              <div>
                <h2 className="text-2xl font-semibold">{detectedAgent.name}</h2>
                <p className="text-gray-300">{detectedAgent.description}</p>
              </div>
              <div className="ml-auto">
                <span className={`px-3 py-1 rounded-full text-sm font-medium text-white ${getAgentTypeColor(detectedAgent.type)}`}>
                  {detectedAgent.type.toUpperCase()}
                </span>
              </div>
            </div>
            
            <div className="grid md:grid-cols-4 gap-4 text-sm">
              <div className="bg-white/5 rounded-lg p-3">
                <div className="text-gray-400">Model Provider</div>
                <div className="font-medium">{detectedAgent.modelProvider}</div>
              </div>
              <div className="bg-white/5 rounded-lg p-3">
                <div className="text-gray-400">Voice Provider</div>
                <div className="font-medium">{detectedAgent.voiceProvider}</div>
              </div>
              <div className="bg-white/5 rounded-lg p-3">
                <div className="text-gray-400">Tools</div>
                <div className="font-medium">{detectedAgent.toolCount}</div>
              </div>
              <div className="bg-white/5 rounded-lg p-3">
                <div className="text-gray-400">Configuration</div>
                <div className="font-medium">
                  {detectedAgent.hasSystemPrompt && detectedAgent.hasFirstMessage ? '✅ Complete' : '⚠️ Incomplete'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-white/10 rounded-lg p-1">
            {[
              { key: 'agents', label: '🤖 My Agents', icon: '🤖' },
              { key: 'templates', label: '📋 Templates', icon: '📋' },
              { key: 'editor', label: '✏️ Editor', icon: '✏️' },
              { key: 'test', label: '🧪 Test', icon: '🧪' },
              { key: 'services', label: '🛠️ Services', icon: '🛠️' },
              { key: 'voice-call', label: '🎤 Voice Call', icon: '🎤' }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-white text-gray-900'
                    : 'text-gray-300 hover:text-white hover:bg-white/10'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white/10 backdrop-blur rounded-lg border border-white/20">
          {/* My Agents Tab */}
          {activeTab === 'agents' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold">🤖 Your Voice Agents</h3>
                <button
                  onClick={() => setShowCreateForm(!showCreateForm)}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  {showCreateForm ? '❌ Cancel' : '➕ Create Agent'}
                </button>
              </div>

              {/* Create Form */}
              {showCreateForm && (
                <div className="mb-6 bg-white/5 rounded-lg p-6 border border-white/10">
                  <h4 className="text-lg font-semibold mb-4">Create New Voice Agent</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Agent Name</label>
                      <input
                        type="text"
                        value={newAgent.name}
                        onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                        placeholder="e.g., My Research Assistant"
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Quick Start Templates</label>
                      <div className="grid md:grid-cols-3 gap-2 mb-4">
                        <button
                          onClick={() => setNewAgent({ 
                            ...newAgent, 
                            name: 'Research Assistant',
                            config_yaml: templates.research
                          })}
                          className="px-3 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg text-green-300 text-sm transition-colors"
                        >
                          🔬 Research Assistant
                        </button>
                        <button
                          onClick={() => setNewAgent({ 
                            ...newAgent, 
                            name: 'Workflow Assistant',
                            config_yaml: templates.workflow
                          })}
                          className="px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg text-blue-300 text-sm transition-colors"
                        >
                          🔧 Workflow Assistant
                        </button>
                        <button
                          onClick={() => setNewAgent({ 
                            ...newAgent, 
                            name: 'Customer Support',
                            config_yaml: templates.support
                          })}
                          className="px-3 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-purple-300 text-sm transition-colors"
                        >
                          🎧 Customer Support
                        </button>
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">YAML Configuration</label>
                      <textarea
                        value={newAgent.config_yaml}
                        onChange={(e) => setNewAgent({ ...newAgent, config_yaml: e.target.value })}
                        placeholder="Paste your YAML configuration here or use a template above..."
                        rows={12}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleCreateAgent}
                        disabled={isSaving}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors"
                      >
                        {isSaving ? '⏳ Creating...' : '🚀 Create Agent'}
                      </button>
                      <button
                        onClick={() => setShowCreateForm(false)}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Voice Agents List */}
              {voiceAgents.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {voiceAgents.map((agent) => (
                    <div key={agent.id} className="bg-white/5 rounded-lg p-6 border border-white/10">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{getAgentTypeIcon(agent.agent_type)}</span>
                          <h4 className="text-lg font-semibold">{agent.name}</h4>
                        </div>
                        <button
                          onClick={() => handleDeleteAgent(agent.id)}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          🗑️
                        </button>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs text-white ${getAgentTypeColor(agent.agent_type)}`}>
                            {agent.agent_type.toUpperCase()}
                          </span>
                        </div>
                        <div className="text-gray-300">
                          <strong>Vapi ID:</strong> {agent.vapi_assistant_id.slice(0, 8)}...
                        </div>
                        <div className="text-gray-400 text-xs">
                          Created: {new Date(agent.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white/5 rounded-lg">
                  <div className="text-6xl mb-4">🤖</div>
                  <h4 className="text-xl font-semibold mb-2">No Voice Agents Yet</h4>
                  <p className="text-gray-400 mb-6">Create your first voice agent to get started</p>
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                  >
                    ➕ Create Your First Agent
                  </button>
                </div>
              )}

              {/* Recent Interactions */}
              {interactions.length > 0 && (
                <div className="mt-8">
                  <h4 className="text-lg font-semibold mb-4">Recent Interactions</h4>
                  <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="max-h-64 overflow-y-auto space-y-3">
                      {interactions.slice(0, 5).map((interaction, index) => (
                        <div key={index} className="border-b border-white/10 pb-3 last:border-b-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-blue-400">{interaction.type}</span>
                            <span className="text-xs text-gray-400">
                              {new Date(interaction.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <div className="text-sm text-gray-300">{interaction.content}</div>
                          {interaction.agent_name && (
                            <div className="text-xs text-gray-500">Agent: {interaction.agent_name}</div>
                          )}
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 text-center">
                      <button
                        onClick={() => router.push('/interactions')}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        View All Interactions →
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Templates Tab */}
          {activeTab === 'templates' && (
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-4">🚀 Quick Start Templates</h3>
              <div className="grid md:grid-cols-3 gap-4">
                <button
                  onClick={() => handleTemplateSelect(templates.research)}
                  className="bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg p-4 text-left transition-colors"
                >
                  <div className="text-2xl mb-2">🔬</div>
                  <h4 className="font-semibold text-green-300">Research Assistant</h4>
                  <p className="text-sm text-gray-400 mt-1">AI-powered research and content generation</p>
                </button>
                
                <button
                  onClick={() => handleTemplateSelect(templates.workflow)}
                  className="bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg p-4 text-left transition-colors"
                >
                  <div className="text-2xl mb-2">🔧</div>
                  <h4 className="font-semibold text-blue-300">Workflow Assistant</h4>
                  <p className="text-sm text-gray-400 mt-1">Business process automation and management</p>
                </button>
                
                <button
                  onClick={() => handleTemplateSelect(templates.support)}
                  className="bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg p-4 text-left transition-colors"
                >
                  <div className="text-2xl mb-2">🎧</div>
                  <h4 className="font-semibold text-purple-300">Customer Support</h4>
                  <p className="text-sm text-gray-400 mt-1">Intelligent customer service and support</p>
                </button>
              </div>
            </div>
          )}

          {/* Editor Tab */}
          {activeTab === 'editor' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">✏️ YAML Configuration Editor</h3>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveConfig}
                    disabled={isSaving}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg transition-colors"
                  >
                    {isSaving ? '⏳ Saving...' : '💾 Save Config'}
                  </button>
                  <button
                    onClick={handleTest}
                    disabled={isTesting}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors"
                  >
                    {isTesting ? '⏳ Testing...' : '🧪 Test'}
                  </button>
                </div>
              </div>
              
              <div className="border border-white/20 rounded-lg overflow-hidden">
                <MonacoEditor
                  height="500px"
                  language="yaml"
                  theme="vs-dark"
                  value={yamlConfig}
                  onChange={(value) => handleConfigChange(value || '')}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    insertSpaces: true,
                    wordWrap: 'on'
                  }}
                />
              </div>
            </div>
          )}

          {/* Test Tab */}
          {activeTab === 'test' && (
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-4">🧪 Test Your Agent</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Test Service</label>
                  <select
                    value={selectedService.id}
                    onChange={(e) => {
                      const service = e.target.value
                      if (service === 'research') {
                        setSelectedService({ id: 'research', port: 8082, configPath: '/health' })
                      } else if (service === 'workflow') {
                        setSelectedService({ id: 'workflow', port: 8083, configPath: '/health' })
                      } else {
                        setSelectedService({ id: 'dynamic', port: 8000, configPath: '/config/yaml' })
                      }
                    }}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="dynamic" className="bg-gray-800">🤖 Main Backend - Configuration Test (Port 8000)</option>
                    <option value="research" className="bg-gray-800">🔬 Research Service - Health Check (Port 8082)</option>
                    <option value="workflow" className="bg-gray-800">🔧 Workflow Service - Health Check (Port 8083)</option>
                  </select>
                </div>

                {/* Test Description */}
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h4 className="font-medium mb-2">Test Description:</h4>
                  {selectedService.id === 'dynamic' && (
                    <p className="text-sm text-gray-300">
                      🤖 <strong>Configuration Test:</strong> Validates your YAML configuration by saving it to the backend and checking system health. This ensures your agent configuration is valid and the main backend is operational.
                    </p>
                  )}
                  {selectedService.id === 'research' && (
                    <p className="text-sm text-gray-300">
                      🔬 <strong>Research Service Health Check:</strong> Tests connectivity to the LangGraph Research Assistant service. This service handles research queries and content generation tasks.
                    </p>
                  )}
                  {selectedService.id === 'workflow' && (
                    <p className="text-sm text-gray-300">
                      🔧 <strong>Workflow Service Health Check:</strong> Tests connectivity to the Workflow Automation service. This service handles business process automation and workflow triggers.
                    </p>
                  )}
                </div>
                
                <button
                  onClick={handleTest}
                  disabled={isTesting}
                  className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors"
                >
                  {isTesting ? '⏳ Running Test...' : `🚀 Run ${selectedService.id === 'dynamic' ? 'Configuration' : 'Health'} Test`}
                </button>
              </div>
            </div>
          )}

          {/* Services Tab */}
          {activeTab === 'services' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-semibold">🛠️ Your Service Configuration</h3>
                  <p className="text-gray-300 text-sm mt-1">
                    Configure your own APIs and services that your voice agents will use
                  </p>
                </div>
                <button
                  onClick={() => setShowServiceForm(!showServiceForm)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  {showServiceForm ? '❌ Cancel' : '➕ Add Service'}
                </button>
              </div>

              {/* Add Service Form */}
              {showServiceForm && (
                <div className="mb-6 bg-white/5 rounded-lg p-6 border border-white/10">
                  <h4 className="text-lg font-semibold mb-4">Add New Service</h4>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Service Name</label>
                      <input
                        type="text"
                        value={newService.service_name}
                        onChange={(e) => setNewService({ ...newService, service_name: e.target.value })}
                        placeholder="e.g., research, workflow, content"
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Service URL</label>
                      <input
                        type="text"
                        value={newService.service_url}
                        onChange={(e) => setNewService({ ...newService, service_url: e.target.value })}
                        placeholder="https://api.yourcompany.com"
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Health Check Path</label>
                      <input
                        type="text"
                        value={newService.health_path}
                        onChange={(e) => setNewService({ ...newService, health_path: e.target.value })}
                        placeholder="/health"
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Timeout (seconds)</label>
                      <input
                        type="number"
                        value={newService.timeout}
                        onChange={(e) => setNewService({ ...newService, timeout: Number(e.target.value) })}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div className="mt-4 flex items-center">
                    <input
                      type="checkbox"
                      id="required"
                      checked={newService.required}
                      onChange={(e) => setNewService({ ...newService, required: e.target.checked })}
                      className="mr-2"
                    />
                    <label htmlFor="required" className="text-sm">Required service (agents won't work without it)</label>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={handleAddService}
                      disabled={!newService.service_name || !newService.service_url}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                    >
                      Add Service
                    </button>
                    <button
                      onClick={() => setShowServiceForm(false)}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Services List */}
              <div className="space-y-4">
                {userServices.length === 0 ? (
                  <div className="text-center py-8 bg-white/5 rounded-lg border border-white/10">
                    <div className="text-4xl mb-4">🛠️</div>
                    <h3 className="text-lg font-semibold mb-2">No Services Configured</h3>
                    <p className="text-gray-400 mb-4">
                      Add your first service to start creating voice agents that use your own APIs
                    </p>
                    <button
                      onClick={() => setShowServiceForm(true)}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                      Add Your First Service
                    </button>
                  </div>
                ) : (
                  userServices.map((service, index) => (
                    <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center">
                            🔗
                          </div>
                          <div>
                            <h4 className="font-semibold capitalize">{service.name}</h4>
                            <p className="text-sm text-gray-400">{service.url}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleTestService(service.name)}
                            disabled={isTestingService[service.name]}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded text-sm transition-colors"
                          >
                            {isTestingService[service.name] ? '🔄 Testing...' : '🧪 Test'}
                          </button>
                          <button
                            onClick={() => handleDeleteService(service.name)}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </div>
                      
                      <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Health Path:</span>
                          <span className="ml-2 font-mono">{service.health_path}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Timeout:</span>
                          <span className="ml-2">{service.timeout}s</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Required:</span>
                          <span className="ml-2">{service.required ? '✅ Yes' : '❌ No'}</span>
                        </div>
                      </div>

                      {/* Test Results */}
                      {serviceTestResults[service.name] && (
                        <div className="mt-3 p-3 bg-white/5 rounded border border-white/10">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium">Test Result:</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              serviceTestResults[service.name].status === 'healthy' 
                                ? 'bg-green-600/20 text-green-300' 
                                : serviceTestResults[service.name].status === 'unhealthy'
                                ? 'bg-yellow-600/20 text-yellow-300'
                                : 'bg-red-600/20 text-red-300'
                            }`}>
                              {serviceTestResults[service.name].status?.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-300">
                            {serviceTestResults[service.name].message}
                          </p>
                          {serviceTestResults[service.name].error && (
                            <p className="text-sm text-red-400 mt-1">
                              Error: {serviceTestResults[service.name].error}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>

              {/* Usage Instructions */}
              {userServices.length > 0 && (
                <div className="mt-8 bg-blue-600/10 rounded-lg p-6 border border-blue-500/20">
                  <h4 className="text-lg font-semibold mb-3">💡 How to Use Your Services</h4>
                  <div className="space-y-2 text-sm">
                    <p>Now you can use these services in your voice agent configurations:</p>
                    <div className="bg-white/5 rounded p-3 font-mono text-xs">
                      <div className="text-gray-400"># In your YAML configuration:</div>
                      <div>tools:</div>
                      <div>  - name: "my_tool"</div>
                      <div>    action:</div>
                      <div className="text-blue-300">      url: "service://{userServices[0]?.name}/endpoint"</div>
                      <div className="text-gray-400"># This will automatically resolve to: {userServices[0]?.url}/endpoint</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Voice Call Tab */}
          {activeTab === 'voice-call' && (
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-4">🎤 Voice Call</h3>
              <VoiceCall />
            </div>
          )}
        </div>

        {/* Test Results */}
        {testResult && (
          <div className={`mt-6 p-4 rounded-lg ${testResult.success ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
            <h4 className="font-semibold mb-2">
              {testResult.success ? '✅ Success' : '❌ Error'}
            </h4>
            <p className="text-sm mb-2">{testResult.message}</p>
            {testResult.data && (
              <pre className="text-xs bg-black/20 p-2 rounded overflow-auto">
                {JSON.stringify(testResult.data, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 