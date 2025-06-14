'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import VoiceCall from './VoiceCall'

interface ServiceStatus {
  online: boolean
  message?: string
  error?: string
}

interface DetectedService {
  id: string
  name: string
  port: number
  description: string
  status: string
  color: string
  isActive: boolean
  url?: string
}

interface AgentInfo {
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

const Dashboard: React.FC = () => {
  const router = useRouter()
  const [detectedServices, setDetectedServices] = useState<DetectedService[]>([])
  const [serviceStatuses, setServiceStatuses] = useState<Record<string, ServiceStatus>>({})
  const [currentAgent, setCurrentAgent] = useState<AgentInfo | null>(null)
  const [currentConfig, setCurrentConfig] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  // Add ref to track if initial load is complete
  const hasInitialized = useRef(false)

  const detectAgentAndServicesFromConfig = useCallback((yamlConfig: string): { agent: AgentInfo; services: DetectedService[] } => {
    const lines = yamlConfig.split('\n')
    const agentInfo: Partial<AgentInfo> = {
      toolCount: 0,
      hasSystemPrompt: false,
      hasFirstMessage: false,
      modelProvider: 'unknown',
      voiceProvider: 'unknown'
    }

    // Extract agent information
    lines.forEach(line => {
      const trimmed = line.trim()
      
      if (trimmed.includes('name:') && !trimmed.startsWith('#')) {
        const value = trimmed.split('name:')[1]?.trim().replace(/["']/g, '')
        if (value) agentInfo.name = value
      }
      
      if (trimmed.includes('provider:') && !trimmed.startsWith('#')) {
        const value = trimmed.split('provider:')[1]?.trim().replace(/["']/g, '')
        if (value) {
          if (line.includes('voice')) {
            agentInfo.voiceProvider = value
          } else {
            agentInfo.modelProvider = value
          }
        }
      }
      
      if (trimmed.includes('system_prompt_template:') || trimmed.includes('systemMessage:')) {
        agentInfo.hasSystemPrompt = true
      }
      
      if (trimmed.includes('firstMessage:')) {
        agentInfo.hasFirstMessage = true
      }
      
      if (trimmed.includes('serverUrl:') || trimmed.includes('server_url:') || trimmed.includes('url:')) {
        const value = trimmed.split(/serverUrl:|server_url:|url:/)[1]?.trim().replace(/["']/g, '')
        if (value) agentInfo.serverUrl = value
      }
    })

    // Count tools
    agentInfo.toolCount = (yamlConfig.match(/- name:/g) || []).length

    // Detect agent type and services based on tools and content
    let type: AgentInfo['type'] = 'unknown'
    let description = 'Custom voice assistant'
    const services: DetectedService[] = []

    // Check for LangGraph Research Assistant
    if (yamlConfig.includes('research_topic') || 
        yamlConfig.includes('generate_content') ||
        yamlConfig.includes('quick-research') ||
        yamlConfig.includes('quick-content') ||
        yamlConfig.includes('ngrok-free.app') ||
        yamlConfig.includes('8082')) {
      type = 'research'
      description = 'AI-powered research and content generation assistant'
      
      // Extract ngrok URL if present
      const ngrokMatch = yamlConfig.match(/https:\/\/[^.]+\.ngrok-free\.app/g)
      const serviceUrl = ngrokMatch ? ngrokMatch[0] : 'http://localhost:8082'
      
      services.push({
        id: 'langgraph',
        name: 'LangGraph Research Assistant',
        port: 8082,
        description: 'AI-powered research and content generation',
        status: '🔬 Research & Content',
        color: 'bg-green-600',
        isActive: true,
        url: serviceUrl
      })
    }

    // Check for Tesseract Engine
    if (yamlConfig.includes('triggerFinancialAnalysisWorkflow') ||
        yamlConfig.includes('processGeneralRequest') ||
        yamlConfig.includes('financial_analysis') ||
        yamlConfig.includes('8081')) {
      type = 'workflow'
      description = 'Workflow automation and business process assistant'
      
      services.push({
        id: 'tesseract',
        name: 'Tesseract Engine',
        port: 8081,
        description: 'Workflow automation and command processing',
        status: '🔧 Workflow Engine',
        color: 'bg-blue-600',
        isActive: true,
        url: 'http://localhost:8081'
      })
    }

    // If custom tools detected
    if (agentInfo.toolCount > 0 && type === 'unknown') {
      type = 'custom'
      description = `Custom assistant with ${agentInfo.toolCount} specialized tools`
    }

    // Always add Vapi Agent Forge as the main backend
    services.push({
      id: 'vapi_forge',
      name: 'Vapi Agent Forge',
      port: 8000,
      description: 'Main backend and configuration management',
      status: '⚙️ Main Backend',
      color: 'bg-purple-600',
      isActive: true,
      url: 'http://localhost:8000'
    })

    const agent: AgentInfo = {
      name: agentInfo.name || 'Unnamed Assistant',
      type,
      description,
      modelProvider: agentInfo.modelProvider || 'unknown',
      voiceProvider: agentInfo.voiceProvider || 'unknown',
      toolCount: agentInfo.toolCount || 0,
      hasSystemPrompt: agentInfo.hasSystemPrompt || false,
      hasFirstMessage: agentInfo.hasFirstMessage || false,
      serverUrl: agentInfo.serverUrl
    }

    return { agent, services }
  }, [])

  const loadCurrentConfig = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/config/yaml')
      const data = await response.json()
      if (data.status === 'success') {
        setCurrentConfig(data.yaml)
        const { agent, services } = detectAgentAndServicesFromConfig(data.yaml)
        setCurrentAgent(agent)
        setDetectedServices(services)
      }
    } catch (error) {
      console.error('Failed to load config:', error)
      // Set default if config loading fails
      setDetectedServices([
        {
          id: 'vapi_forge',
          name: 'Vapi Agent Forge',
          port: 8000,
          description: 'Main backend and configuration management',
          status: '⚙️ Main Backend',
          color: 'bg-purple-600',
          isActive: true,
          url: 'http://localhost:8000'
        }
      ])
    }
  }, [detectAgentAndServicesFromConfig])

  const checkServiceStatus = useCallback(async (service: DetectedService) => {
    try {
      // Use the backend proxy for service status checks
      const response = await fetch(`http://localhost:8000/service-status/${service.id}`, { 
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      })
      const data = await response.json()
      
      setServiceStatuses(prev => ({
        ...prev,
        [service.id]: { 
          online: data.online || false, 
          message: data.message || (data.online ? 'Running' : 'Offline'),
          error: data.error
        }
      }))
    } catch (error) {
      setServiceStatuses(prev => ({
        ...prev,
        [service.id]: { 
          online: false, 
          error: (error as Error).message 
        }
      }))
    }
  }, [])

  const refreshAllStatuses = useCallback(async () => {
    setIsLoading(true)
    
    try {
      // Load config first
      const response = await fetch('http://localhost:8000/config/yaml')
      const data = await response.json()
      
      if (data.status === 'success') {
        setCurrentConfig(data.yaml)
        const { agent, services } = detectAgentAndServicesFromConfig(data.yaml)
        setCurrentAgent(agent)
        setDetectedServices(services)
        
        // Check status for all services
        for (const service of services) {
          try {
            const statusResponse = await fetch(`http://localhost:8000/service-status/${service.id}`)
            const statusData = await statusResponse.json()
            
            setServiceStatuses(prev => ({
              ...prev,
              [service.id]: { 
                online: statusData.online || false, 
                message: statusData.message || (statusData.online ? 'Running' : 'Offline'),
                error: statusData.error
              }
            }))
          } catch (error) {
            setServiceStatuses(prev => ({
              ...prev,
              [service.id]: { 
                online: false, 
                error: (error as Error).message 
              }
            }))
          }
        }
      }
    } catch (error) {
      console.error('Failed to refresh statuses:', error)
      // Set default if config loading fails
      setDetectedServices([
        {
          id: 'vapi_forge',
          name: 'Vapi Agent Forge',
          port: 8000,
          description: 'Main backend and configuration management',
          status: '⚙️ Main Backend',
          color: 'bg-purple-600',
          isActive: true,
          url: 'http://localhost:8000'
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }, [detectAgentAndServicesFromConfig]) // Only depend on the detection function

  // Initial load - run only once
  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true
      refreshAllStatuses()
    }
  }, []) // Empty dependency array

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

  const StatusIndicator: React.FC<{ status: ServiceStatus }> = ({ status }) => (
    <div className={`w-4 h-4 rounded-full ${status.online ? 'bg-green-500' : 'bg-red-500'}`} />
  )

  const ServiceStatusCard: React.FC<{ service: DetectedService }> = ({ service }) => {
    const status = serviceStatuses[service.id] || { online: false }
    
    return (
      <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
        <div className="flex items-center justify-between mb-4">
          <StatusIndicator status={status} />
          <h3 className="text-xl font-semibold">{service.name}</h3>
        </div>
        <p className="text-gray-300 mb-2">{service.description}</p>
        <p className="text-gray-400 mb-4">Port {service.port}</p>
        <div className="flex items-center justify-between mb-4">
          <span className={`px-2 py-1 rounded text-xs text-white ${service.color}`}>
            {service.status}
          </span>
          <span className="text-xs text-green-400">
            ✅ Active in Config
          </span>
        </div>
        <button
          onClick={() => checkServiceStatus(service)}
          className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Check Status
        </button>
        {status.message && (
          <p className="mt-2 text-green-400 text-sm">{status.message}</p>
        )}
        {status.error && (
          <p className="mt-2 text-red-400 text-sm">{status.error}</p>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            🤖 Dynamic Voice Agent Dashboard
          </h1>
          <p className="text-lg text-gray-300">
            Real-time monitoring of your voice agent system
          </p>
        </div>

        {/* Current Agent Overview */}
        {currentAgent && (
          <div className="mb-12">
            <h2 className="text-2xl font-semibold mb-6 flex items-center">
              {getAgentTypeIcon(currentAgent.type)} Current Voice Agent
            </h2>
            <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{getAgentTypeIcon(currentAgent.type)}</span>
                    <span className="font-medium text-white">{currentAgent.name}</span>
                  </div>
                  <p className="text-sm text-gray-300">{currentAgent.description}</p>
                  <span className={`inline-block mt-2 px-2 py-1 rounded text-xs text-white ${getAgentTypeColor(currentAgent.type)}`}>
                    {currentAgent.type.toUpperCase()}
                  </span>
                </div>
                
                <div className="bg-white/10 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Configuration</h4>
                  <div className="space-y-1 text-sm">
                    <div className="text-gray-300">Tools: {currentAgent.toolCount}</div>
                    <div className="text-gray-300">Model: {currentAgent.modelProvider}</div>
                    <div className="text-gray-300">Voice: {currentAgent.voiceProvider}</div>
                  </div>
                </div>
                
                <div className="bg-white/10 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Status</h4>
                  <div className="space-y-1 text-sm">
                    <div className={currentAgent.hasSystemPrompt ? 'text-green-400' : 'text-red-400'}>
                      {currentAgent.hasSystemPrompt ? '✅' : '❌'} System Prompt
                    </div>
                    <div className={currentAgent.hasFirstMessage ? 'text-green-400' : 'text-red-400'}>
                      {currentAgent.hasFirstMessage ? '✅' : '❌'} First Message
                    </div>
                    <div className="text-green-400">
                      ✅ {detectedServices.filter(s => s.isActive).length} Services
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/10 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Actions</h4>
                  <div className="space-y-2">
                    <button
                      onClick={() => router.push('/agents')}
                      className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                    >
                      📝 Edit Agent
                    </button>
                    <button
                      onClick={refreshAllStatuses}
                      disabled={isLoading}
                      className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white text-sm rounded transition-colors"
                    >
                      {isLoading ? 'Refreshing...' : '🔄 Refresh'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Dynamic System Status */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 flex items-center">
            📊 System Status
            {detectedServices.length > 0 && (
              <span className="ml-4 text-sm text-green-400">
                • {detectedServices.filter(s => s.isActive).length} services detected
              </span>
            )}
          </h2>
          
          {detectedServices.length > 0 ? (
            <div className="grid md:grid-cols-3 gap-6">
              {detectedServices.map((service) => (
                <ServiceStatusCard key={service.id} service={service} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold mb-2">No Voice Agent Configured</h3>
              <p className="text-gray-400 mb-6">Create your first voice agent to see system status</p>
              <button
                onClick={() => router.push('/agents')}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                Create Voice Agent
              </button>
            </div>
          )}

          {/* Configuration Summary */}
          {detectedServices.length > 0 && currentAgent && (
            <div className="mt-6 bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
              <h4 className="text-blue-300 font-medium mb-2">📋 Configuration Summary:</h4>
              <div className="text-blue-200 text-sm space-y-1">
                <div>• <strong>Agent:</strong> {currentAgent.name} ({currentAgent.type})</div>
                <div>• <strong>Tools:</strong> {currentAgent.toolCount} configured</div>
                <div>• <strong>Services:</strong> {detectedServices.filter(s => s.isActive).map(s => s.name).join(', ')}</div>
                <div>• <strong>Model:</strong> {currentAgent.modelProvider} | <strong>Voice:</strong> {currentAgent.voiceProvider}</div>
              </div>
              <div className="mt-3 text-xs text-blue-300">
                💡 All information auto-detected from your YAML configuration. 
                <button 
                  onClick={() => router.push('/agents')}
                  className="ml-1 underline hover:text-blue-200"
                >
                  Edit configuration
                </button> to change services.
              </div>
            </div>
          )}
        </div>

        {/* Voice Call Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 flex items-center">
            📞 Voice Assistant Test
          </h2>
          <VoiceCall 
            onCallStart={() => console.log('🚀 Voice call started from dashboard')}
            onCallEnd={() => console.log('🔚 Voice call ended from dashboard')}
            onTranscript={(transcript) => console.log('📝 Transcript:', transcript)}
          />
        </div>

        {/* Quick Actions */}
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
          <div className="flex flex-wrap gap-4 justify-center">
            <button
              onClick={() => router.push('/agents')}
              className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              🤖 Manage Agents
            </button>
            <button
              onClick={refreshAllStatuses}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {isLoading ? 'Refreshing...' : '🔄 Refresh Status'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard 