'use client'

import React, { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import ResponseRenderer from '@/components/ResponseRenderer'
import ConfigTemplates from '@/components/ConfigTemplates'
import ServiceSelector from '@/components/ServiceSelector'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

interface AgentConfig {
  name: string
  type: string
  description: string
  tools: number
  lastModified: string
  isActive: boolean
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
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'service' | 'templates' | 'editor' | 'test' | 'agents'>('agents')
  const [selectedService, setSelectedService] = useState<{id: string, port: number, configPath: string}>({
    id: 'dynamic',
    port: 8000,
    configPath: '/config/yaml'
  })
  const [detectedAgent, setDetectedAgent] = useState<DetectedAgentInfo | null>(null)
  const [savedAgents, setSavedAgents] = useState<AgentConfig[]>([])

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

  const handleServiceChange = (serviceId: string, port: number, configPath: string) => {
    setSelectedService({ id: serviceId, port, configPath })
  }

  const handleTemplateSelect = (template: string) => {
    setYamlConfig(template)
    setActiveTab('editor')
    setTestResult(null)
    // Update detected agent info
    const agentInfo = detectAgentFromConfig(template)
    setDetectedAgent(agentInfo)
  }

  const handleConfigChange = (value: string) => {
    setYamlConfig(value)
    // Update detected agent info in real-time
    const agentInfo = detectAgentFromConfig(value)
    setDetectedAgent(agentInfo)
  }

  const handleSave = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/config/yaml', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml: yamlConfig })
      })
      
      const result = await response.json()
      setTestResult({
        success: response.ok,
        message: response.ok ? 'Agent saved successfully!' : 'Failed to save agent',
        data: result
      })

      // If successful, add to saved agents list
      if (response.ok && detectedAgent) {
        const newAgent: AgentConfig = {
          name: detectedAgent.name,
          type: detectedAgent.type,
          description: detectedAgent.description,
          tools: detectedAgent.toolCount,
          lastModified: new Date().toISOString(),
          isActive: true
        }
        setSavedAgents(prev => {
          const filtered = prev.filter(agent => agent.name !== newAgent.name)
          return [newAgent, ...filtered]
        })
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Error saving agent',
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
    setIsLoading(false)
  }

  const handleTest = async () => {
    setIsLoading(true)
    try {
      // Test the configuration by validating YAML and checking backend connectivity
      const response = await fetch('http://localhost:8000/config/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml: yamlConfig })
      })
      
      const result = await response.json()
      setTestResult({
        success: response.ok,
        message: response.ok ? 'Configuration is valid!' : 'Configuration has errors',
        data: result,
        validation: true
      })
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Error testing configuration - make sure backend is running on port 8000',
        error: error instanceof Error ? error.message : 'Unknown error',
        validation: true
      })
    }
    setIsLoading(false)
  }

  // Initialize detected agent info
  useEffect(() => {
    const agentInfo = detectAgentFromConfig(yamlConfig)
    setDetectedAgent(agentInfo)
  }, [])

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

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Dynamic Voice Agent Builder</h1>
        <p className="text-gray-300">Create and configure unlimited voice agents with custom capabilities</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab('agents')}
          className={`px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
            activeTab === 'agents'
              ? 'bg-indigo-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          🤖 My Agents
        </button>
        <button
          onClick={() => setActiveTab('service')}
          className={`px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
            activeTab === 'service'
              ? 'bg-purple-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          🔧 Service
        </button>
        <button
          onClick={() => setActiveTab('templates')}
          className={`px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
            activeTab === 'templates'
              ? 'bg-green-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          🚀 Templates
        </button>
        <button
          onClick={() => setActiveTab('editor')}
          className={`px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
            activeTab === 'editor'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          📝 YAML Editor
        </button>
        <button
          onClick={() => setActiveTab('test')}
          className={`px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
            activeTab === 'test'
              ? 'bg-orange-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          🧪 Test Results
        </button>
      </div>

      {/* My Agents Section */}
      {activeTab === 'agents' && (
        <div className="space-y-6">
          {/* Current Agent Preview */}
          {detectedAgent && (
            <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-4">Current Agent Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{getAgentTypeIcon(detectedAgent.type)}</span>
                    <span className="font-medium text-white">{detectedAgent.name}</span>
                  </div>
                  <p className="text-sm text-gray-300">{detectedAgent.description}</p>
                  <span className={`inline-block mt-2 px-2 py-1 rounded text-xs text-white ${getAgentTypeColor(detectedAgent.type)}`}>
                    {detectedAgent.type.toUpperCase()}
                  </span>
                </div>
                
                <div className="bg-white/10 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Tools & Features</h4>
                  <div className="space-y-1 text-sm">
                    <div className="text-gray-300">Tools: {detectedAgent.toolCount}</div>
                    <div className={detectedAgent.hasSystemPrompt ? 'text-green-400' : 'text-red-400'}>
                      {detectedAgent.hasSystemPrompt ? '✅' : '❌'} System Prompt
                    </div>
                    <div className={detectedAgent.hasFirstMessage ? 'text-green-400' : 'text-red-400'}>
                      {detectedAgent.hasFirstMessage ? '✅' : '❌'} First Message
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/10 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">AI Configuration</h4>
                  <div className="space-y-1 text-sm text-gray-300">
                    <div>Model: {detectedAgent.modelProvider}</div>
                    <div>Voice: {detectedAgent.voiceProvider}</div>
                  </div>
                </div>
                
                <div className="bg-white/10 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Actions</h4>
                  <div className="space-y-2">
                    <button
                      onClick={() => setActiveTab('editor')}
                      className="w-full px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                    >
                      Edit Config
                    </button>
                    <button
                      onClick={handleTest}
                      disabled={isLoading}
                      className="w-full px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white text-sm rounded transition-colors"
                    >
                      {isLoading ? 'Testing...' : 'Test'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Saved Agents List */}
          <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white mb-4">Saved Voice Agents</h3>
            {savedAgents.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedAgents.map((agent, index) => (
                  <div key={index} className="bg-white/10 rounded-lg p-4 border border-white/20">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{getAgentTypeIcon(agent.type)}</span>
                        <span className="font-medium text-white">{agent.name}</span>
                      </div>
                      <span className={agent.isActive ? 'text-green-400' : 'text-gray-400'}>
                        {agent.isActive ? '🟢' : '⚪'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2">{agent.description}</p>
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>{agent.tools} tools</span>
                      <span>{new Date(agent.lastModified).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-400 mb-4">No saved agents yet</p>
                <button
                  onClick={() => setActiveTab('templates')}
                  className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  Create Your First Agent
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Service Selection Section */}
      {activeTab === 'service' && (
        <div className="space-y-6">
          <ServiceSelector onServiceChange={handleServiceChange} />
          <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white mb-4">Current Selection</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Service:</span>
                <span className="ml-2 text-white font-medium">{selectedService.id}</span>
              </div>
              <div>
                <span className="text-gray-400">Port:</span>
                <span className="ml-2 text-white font-medium">{selectedService.port}</span>
              </div>
              <div>
                <span className="text-gray-400">Config Path:</span>
                <span className="ml-2 text-white font-medium">{selectedService.configPath}</span>
              </div>
            </div>
            <div className="mt-4 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg">
              <p className="text-blue-200 text-sm">
                💡 <strong>Dynamic Agent System:</strong> Create unlimited voice agents with custom tools and capabilities. 
                The system automatically detects agent types and optimizes configurations for voice interactions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Templates Section */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <ConfigTemplates onTemplateSelect={handleTemplateSelect} />
        </div>
      )}

      {/* Editor Section */}
      {activeTab === 'editor' && (
        <div className="lg:col-span-2">
          <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Voice Agent Configuration</h2>
              <div className="flex space-x-4">
                <button
                  onClick={handleTest}
                  disabled={isLoading}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg transition-colors"
                >
                  {isLoading ? 'Testing...' : 'Test Config'}
                </button>
                <button
                  onClick={handleSave}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors"
                >
                  {isLoading ? 'Saving...' : 'Save Agent'}
                </button>
              </div>
            </div>

            <div className="border border-white/10 rounded-lg overflow-hidden">
              <MonacoEditor
                height="500px"
                language="yaml"
                value={yamlConfig}
                onChange={(value) => handleConfigChange(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  wordWrap: 'on',
                  automaticLayout: true,
                }}
              />
            </div>

            {/* Real-time Agent Info */}
            {detectedAgent && (
              <div className="mt-4 p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
                <h4 className="text-green-300 font-medium mb-2">🤖 Detected Agent Configuration:</h4>
                <div className="text-green-200 text-sm grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <strong>Name:</strong> {detectedAgent.name}<br/>
                    <strong>Type:</strong> {detectedAgent.type}
                  </div>
                  <div>
                    <strong>Tools:</strong> {detectedAgent.toolCount}<br/>
                    <strong>Model:</strong> {detectedAgent.modelProvider}
                  </div>
                  <div>
                    <strong>Voice:</strong> {detectedAgent.voiceProvider}<br/>
                    <strong>Ready:</strong> {detectedAgent.hasSystemPrompt && detectedAgent.hasFirstMessage ? '✅' : '⚠️'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Test Results Section */}
      {activeTab === 'test' && (
        <div className="space-y-6">
          <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">Configuration Test Results</h2>
            
            {!testResult ? (
              <div className="text-center py-8">
                <p className="text-gray-400 mb-4">No test results yet. Run a test to validate your agent configuration.</p>
                <button
                  onClick={handleTest}
                  disabled={isLoading}
                  className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg transition-colors"
                >
                  {isLoading ? 'Testing...' : 'Run Validation Test'}
                </button>
              </div>
            ) : (
              <ResponseRenderer data={testResult} title="Agent Configuration Test Results" />
            )}
          </div>
        </div>
      )}
    </div>
  )
} 