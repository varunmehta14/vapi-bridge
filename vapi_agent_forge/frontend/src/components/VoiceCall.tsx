'use client'

import React, { useEffect, useRef, useState } from 'react'

interface User {
  id: number
  username: string
}

interface VoiceAgent {
  id: number
  name: string
  vapi_assistant_id: string
  agent_type: string
}

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  type: 'transcript' | 'function-call' | 'system'
}

const VoiceCall: React.FC = () => {
  const vapiRef = useRef<any>(null)
  const isInitialized = useRef(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isCallActive, setIsCallActive] = useState(false)
  const [callStatus, setCallStatus] = useState<string>('Ready')
  const [user, setUser] = useState<User | null>(null)
  const [voiceAgents, setVoiceAgents] = useState<VoiceAgent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<VoiceAgent | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentTranscript, setCurrentTranscript] = useState('')
  const [isMuted, setIsMuted] = useState(false)
  const [vapiError, setVapiError] = useState<string | null>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isInitialized.current) return
    
    const userData = localStorage.getItem('user')
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
      loadUserVoiceAgents(parsedUser.id)
    }
    
    isInitialized.current = true
  }, [])

  // Initialize VAPI when user is loaded
  useEffect(() => {
    if (user && !vapiRef.current) {
      initializeVapi()
    }
  }, [user])

  const addMessage = (role: 'user' | 'assistant' | 'system', content: string, type: 'transcript' | 'function-call' | 'system' = 'transcript') => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date(),
      type
    }
    setMessages(prev => [...prev, newMessage])
  }

  const loadUserVoiceAgents = async (userId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/users/${userId}/voice-agents`)
      const data = await response.json()
      if (data.status === 'success' && data.voice_agents.length > 0) {
        setVoiceAgents(data.voice_agents)
        setSelectedAgent(data.voice_agents[0]) // Select first agent by default
      }
    } catch (error) {
      console.error('Failed to load voice agents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const initializeVapi = async () => {
    try {
      setVapiError(null) // Clear any previous errors
      
      if (!user) {
        throw new Error('User not logged in')
      }

      // Get user's Vapi public key
      const response = await fetch(`http://localhost:8000/users/${user.id}/vapi-public-key`)
      
      if (!response.ok) {
        if (response.status === 400) {
          throw new Error('VAPI public key not configured. Please add your VAPI public key in the login settings.')
        }
        throw new Error('Failed to get VAPI public key')
      }
      
      const data = await response.json()
      
      if (!data.public_key) {
        throw new Error('No Vapi public key available for this user. Please add your VAPI public key in settings.')
      }

      // Dynamically import Vapi
      const { default: Vapi } = await import('@vapi-ai/web')
      
      vapiRef.current = new Vapi(data.public_key)
      
      // Set up event listeners
      vapiRef.current.on('call-start', () => {
        console.log('📞 Call started')
        setIsCallActive(true)
        setCallStatus('Call Active')
        setMessages([]) // Clear previous messages
        addMessage('system', 'Call started', 'system')
        logInteraction('call_started', 'Voice call initiated')
      })

      vapiRef.current.on('call-end', () => {
        console.log('📞 Call ended')
        setIsCallActive(false)
        setCallStatus('Call Ended')
        setCurrentTranscript('')
        addMessage('system', 'Call ended', 'system')
        logInteraction('call_ended', 'Voice call ended')
      })

      vapiRef.current.on('speech-start', () => {
        console.log('🎤 User started speaking')
        setCallStatus('User Speaking')
      })

      vapiRef.current.on('speech-end', () => {
        console.log('🎤 User stopped speaking')
        setCallStatus('Processing...')
      })

      vapiRef.current.on('message', (message: any) => {
        console.log('💬 Message:', message)
        
        if (message.type === 'transcript') {
          const content = message.transcript || message.text
          if (content) {
            if (message.transcriptType === 'partial') {
              // Show live transcript for user
              if (message.role === 'user') {
                setCurrentTranscript(content)
              }
            } else if (message.transcriptType === 'final') {
              // Add final transcript to messages
              setCurrentTranscript('')
              addMessage(message.role, content, 'transcript')
              logInteraction('user_message', content)
            }
          }
        }
        
        if (message.type === 'function-call') {
          const functionName = message.functionCall?.name || 'Unknown function'
          const params = message.functionCall?.parameters || {}
          const functionText = `🔧 Called: ${functionName}${Object.keys(params).length > 0 ? ` with ${JSON.stringify(params)}` : ''}`
          addMessage('system', functionText, 'function-call')
          logInteraction('function_call', functionText)
        }
      })

      vapiRef.current.on('error', (error: any) => {
        console.error('❌ Vapi error:', error)
        setCallStatus('Error: ' + error.message)
        addMessage('system', `Error: ${error.message}`, 'system')
        logInteraction('error', `Error: ${error.message}`)
      })

      console.log('✅ Vapi initialized successfully')
      setCallStatus('Ready')
      
    } catch (error) {
      console.error('❌ Failed to initialize Vapi:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      setVapiError(errorMessage)
      setCallStatus('Initialization Failed')
    }
  }

  const logInteraction = async (type: string, content: string) => {
    if (!user || !selectedAgent) return
    
    try {
      await fetch(`http://localhost:8000/users/${user.id}/interactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          voice_agent_id: selectedAgent.id,
          interaction_type: type,
          content: content
        }),
      })
    } catch (error) {
      console.error('Failed to log interaction:', error)
    }
  }

  const startCall = async () => {
    if (!vapiRef.current || !selectedAgent) {
      console.error('❌ Vapi not initialized or no agent selected')
      return
    }

    try {
      setCallStatus('Starting Call...')
      
      await vapiRef.current.start(selectedAgent.vapi_assistant_id)
      
      console.log('📞 Call started with agent:', selectedAgent.name)
      
    } catch (error) {
      console.error('❌ Failed to start call:', error)
      setCallStatus('Failed to Start Call')
      addMessage('system', `Failed to start call: ${error}`, 'system')
    }
  }

  const endCall = () => {
    if (vapiRef.current && isCallActive) {
      vapiRef.current.stop()
      console.log('📞 Call ended by user')
    }
  }

  const toggleMute = () => {
    if (vapiRef.current) {
      const newMutedState = !isMuted
      vapiRef.current.setMuted(newMutedState)
      setIsMuted(newMutedState)
      addMessage('system', newMutedState ? 'Microphone muted' : 'Microphone unmuted', 'system')
    }
  }

  const getStatusColor = () => {
    if (isCallActive) return 'text-green-400'
    if (callStatus.includes('Error') || callStatus.includes('Failed')) return 'text-red-400'
    if (callStatus === 'Ready') return 'text-blue-400'
    return 'text-yellow-400'
  }

  const getAgentTypeIcon = (type: string) => {
    switch (type) {
      case 'research': return '🔬'
      case 'workflow': return '🔧'
      case 'custom': return '⚙️'
      default: return '🤖'
    }
  }

  const getMessageIcon = (message: Message) => {
    if (message.type === 'system') return '🔔'
    if (message.type === 'function-call') return '🔧'
    if (message.role === 'user') return '👤'
    if (message.role === 'assistant') return '🤖'
    return '💬'
  }

  const getMessageColor = (message: Message) => {
    if (message.type === 'system') return 'text-gray-400'
    if (message.type === 'function-call') return 'text-yellow-400'
    if (message.role === 'user') return 'text-blue-400'
    if (message.role === 'assistant') return 'text-green-400'
    return 'text-white'
  }

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="text-yellow-400 mb-2">⏳ Loading voice agents...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-8">
        <div className="text-red-400 mb-2">❌ Please log in to use voice agents</div>
      </div>
    )
  }

  if (vapiError) {
    return (
      <div className="text-center py-8">
        <div className="text-6xl mb-4">⚠️</div>
        <h3 className="text-xl font-semibold mb-2 text-red-400">VAPI Configuration Error</h3>
        <p className="text-gray-400 mb-6 max-w-md mx-auto">{vapiError}</p>
        <div className="space-y-3">
          <button
            onClick={() => window.location.href = '/login'}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors block mx-auto"
          >
            🔑 Update VAPI Keys
          </button>
          <button
            onClick={() => {
              setVapiError(null)
              initializeVapi()
            }}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors block mx-auto"
          >
            🔄 Retry Initialization
          </button>
        </div>
      </div>
    )
  }

  if (voiceAgents.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-6xl mb-4">🤖</div>
        <h3 className="text-xl font-semibold mb-2">No Voice Agents</h3>
        <p className="text-gray-400 mb-4">Create your first voice agent to start voice conversations</p>
        <button
          onClick={() => window.location.href = '/voice-agents'}
          className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
        >
          ➕ Create Voice Agent
        </button>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Left Panel - Controls */}
      <div className="space-y-6">
        {/* Agent Selection */}
        <div>
          <label className="block text-sm font-medium mb-2">Select Voice Agent</label>
          <select
            value={selectedAgent?.id || ''}
            onChange={(e) => {
              const agent = voiceAgents.find(a => a.id === parseInt(e.target.value))
              setSelectedAgent(agent || null)
            }}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {voiceAgents.map((agent) => (
              <option key={agent.id} value={agent.id} className="bg-gray-800">
                {getAgentTypeIcon(agent.agent_type)} {agent.name} ({agent.agent_type})
              </option>
            ))}
          </select>
        </div>

        {/* Selected Agent Info */}
        {selectedAgent && (
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{getAgentTypeIcon(selectedAgent.agent_type)}</span>
              <h3 className="font-semibold">{selectedAgent.name}</h3>
              <span className="px-2 py-1 bg-blue-600 text-xs rounded text-white">
                {selectedAgent.agent_type.toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-gray-400">
              Assistant ID: {selectedAgent.vapi_assistant_id.slice(0, 8)}...
            </p>
          </div>
        )}

        {/* Call Controls */}
        <div className="text-center space-y-4">
          <div className={`text-lg font-medium ${getStatusColor()}`}>
            Status: {callStatus}
          </div>
          
          <div className="flex justify-center gap-4">
            {!isCallActive ? (
              <button
                onClick={startCall}
                disabled={!selectedAgent || callStatus.includes('Failed')}
                className="px-8 py-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg font-semibold text-lg transition-colors flex items-center gap-2"
              >
                📞 Start Call
              </button>
            ) : (
              <>
                <button
                  onClick={toggleMute}
                  className={`px-6 py-3 ${isMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-yellow-600 hover:bg-yellow-700'} text-white rounded-lg font-semibold transition-colors flex items-center gap-2`}
                >
                  {isMuted ? '🔇 Unmute' : '🎤 Mute'}
                </button>
                <button
                  onClick={endCall}
                  className="px-8 py-4 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold text-lg transition-colors flex items-center gap-2"
                >
                  📞 End Call
                </button>
              </>
            )}
          </div>

          {/* Instructions */}
          <div className="text-sm text-gray-400 max-w-md mx-auto">
            {!isCallActive ? (
              <p>Select a voice agent and click "Start Call" to begin your conversation. Make sure your microphone is enabled.</p>
            ) : (
              <p>Speak naturally. The AI will respond through your speakers. Use the mute button to pause your microphone.</p>
            )}
          </div>
        </div>

        {/* User Info */}
        <div className="text-center text-xs text-gray-500">
          Logged in as: {user.username} | {voiceAgents.length} voice agent{voiceAgents.length !== 1 ? 's' : ''} available
        </div>
      </div>

      {/* Right Panel - Live Transcript */}
      <div className="bg-white/5 rounded-lg border border-white/10 flex flex-col h-[600px]">
        <div className="p-4 border-b border-white/10">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            💬 Live Conversation
            {isCallActive && <span className="text-green-400 text-sm">(Live)</span>}
          </h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              <div className="text-4xl mb-2">🎤</div>
              <p>Start a call to see live transcripts and interactions</p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="flex gap-3">
                <span className="text-lg mt-1">{getMessageIcon(message)}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`font-medium ${getMessageColor(message)}`}>
                      {message.role === 'user' ? 'You' : 
                       message.role === 'assistant' ? 'Assistant' : 
                       'System'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className={`text-sm ${getMessageColor(message)}`}>
                    {message.content}
                  </p>
                </div>
              </div>
            ))
          )}
          
          {/* Live transcript indicator */}
          {currentTranscript && (
            <div className="flex gap-3 opacity-70">
              <span className="text-lg mt-1">👤</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-blue-400">You</span>
                  <span className="text-xs text-gray-500">speaking...</span>
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
                    <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse delay-75"></div>
                    <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse delay-150"></div>
                  </div>
                </div>
                <p className="text-sm text-blue-400 italic">
                  {currentTranscript}
                </p>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  )
}

export default VoiceCall 