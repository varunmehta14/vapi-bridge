'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Vapi from '@vapi-ai/web'

interface VoiceCallProps {
  assistantId?: string
  publicKey?: string
  onCallStart?: () => void
  onCallEnd?: () => void
  onTranscript?: (transcript: { role: string; content: string }) => void
}

interface CallStatus {
  isConnected: boolean
  isActive: boolean
  isMuted: boolean
  duration: number
  status: string
}

const VoiceCall: React.FC<VoiceCallProps> = ({
  assistantId = 'e3ee5d86-2fef-43a6-a4e1-07d1cb47bb10', // Default to new web-optimized assistant ID
  publicKey, // Will be fetched from backend if not provided
  onCallStart,
  onCallEnd,
  onTranscript
}) => {
  const [vapi, setVapi] = useState<Vapi | null>(null)
  const [callStatus, setCallStatus] = useState<CallStatus>({
    isConnected: false,
    isActive: false,
    isMuted: false,
    duration: 0,
    status: 'idle'
  })
  const [transcript, setTranscript] = useState<Array<{ role: string; content: string; timestamp: Date }>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [volumeLevel, setVolumeLevel] = useState(0)

  // Fetch public key if not provided
  const fetchPublicKey = useCallback(async () => {
    if (publicKey) return publicKey
    
    try {
      const response = await fetch('http://localhost:8000/vapi/public-key')
      const data = await response.json()
      return data.public_key
    } catch (error) {
      console.error('Failed to fetch public key:', error)
      throw new Error('Failed to get Vapi public key')
    }
  }, [publicKey])

  // Initialize Vapi
  const initializeVapi = useCallback(async () => {
    try {
      const key = await fetchPublicKey()
      if (!key) {
        throw new Error('No Vapi public key available')
      }

      const vapiInstance = new Vapi(key)
      
      // Set up event listeners
      vapiInstance.on('call-start', () => {
        console.log('📞 Call started')
        setCallStatus(prev => ({ ...prev, isActive: true, isConnected: true, status: 'active' }))
        setError(null)
        onCallStart?.()
      })

      vapiInstance.on('call-end', () => {
        console.log('📞 Call ended')
        setCallStatus(prev => ({ 
          ...prev, 
          isActive: false, 
          isConnected: false, 
          status: 'ended',
          duration: 0 
        }))
        onCallEnd?.()
      })

      vapiInstance.on('speech-start', () => {
        console.log('🗣️ Speech started')
      })

      vapiInstance.on('speech-end', () => {
        console.log('🤐 Speech ended')
      })

      vapiInstance.on('volume-level', (level: number) => {
        setVolumeLevel(level)
      })

      vapiInstance.on('message', (message: any) => {
        console.log('📨 Message received:', message)
        
        if (message.type === 'transcript' && message.transcript) {
          const transcriptEntry = {
            role: message.role || 'assistant',
            content: message.transcript,
            timestamp: new Date()
          }
          setTranscript(prev => [...prev, transcriptEntry])
          onTranscript?.(transcriptEntry)
        }
        
        if (message.type === 'function-call') {
          console.log('🔧 Function call:', message.functionCall)
        }
      })

      vapiInstance.on('error', (error: any) => {
        console.error('❌ Vapi error:', error)
        setError(error.message || 'An error occurred during the call')
        setIsLoading(false)
        setCallStatus(prev => ({ 
          ...prev, 
          isActive: false, 
          isConnected: false, 
          status: 'error' 
        }))
      })

      setVapi(vapiInstance)
      console.log('✅ Vapi initialized successfully')
    } catch (error) {
      console.error('Failed to initialize Vapi:', error)
      setError((error as Error).message)
    }
  }, [fetchPublicKey, onCallStart, onCallEnd, onTranscript])

  // Start call
  const startCall = useCallback(async () => {
    if (!vapi) {
      setError('Vapi not initialized')
      return
    }

    setIsLoading(true)
    setError(null)
    setTranscript([])
    
    try {
      setCallStatus(prev => ({ ...prev, status: 'connecting' }))
      
      // Start the call with assistant ID
      await vapi.start(assistantId)
      
      console.log('📞 Starting call with assistant:', assistantId)
    } catch (error) {
      console.error('Failed to start call:', error)
      setError((error as Error).message)
      setIsLoading(false)
      setCallStatus(prev => ({ ...prev, status: 'error' }))
    }
  }, [vapi, assistantId])

  // Stop call
  const stopCall = useCallback(() => {
    if (!vapi) return

    try {
      vapi.stop()
      setIsLoading(false)
      console.log('📞 Call stopped')
    } catch (error) {
      console.error('Failed to stop call:', error)
      setError((error as Error).message)
    }
  }, [vapi])

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (!vapi) return

    try {
      const newMuteState = !callStatus.isMuted
      vapi.setMuted(newMuteState)
      setCallStatus(prev => ({ ...prev, isMuted: newMuteState }))
      console.log(`🔇 ${newMuteState ? 'Muted' : 'Unmuted'}`)
    } catch (error) {
      console.error('Failed to toggle mute:', error)
      setError((error as Error).message)
    }
  }, [vapi, callStatus.isMuted])

  // Duration timer
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    if (callStatus.isActive) {
      interval = setInterval(() => {
        setCallStatus(prev => ({ ...prev, duration: prev.duration + 1 }))
      }, 1000)
    } else {
      setCallStatus(prev => ({ ...prev, duration: 0 }))
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [callStatus.isActive])

  // Initialize on mount
  useEffect(() => {
    initializeVapi()
  }, [initializeVapi])

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Get status color
  const getStatusColor = () => {
    switch (callStatus.status) {
      case 'active': return 'text-green-400'
      case 'connecting': return 'text-yellow-400'
      case 'error': return 'text-red-400'
      case 'ended': return 'text-gray-400'
      default: return 'text-gray-400'
    }
  }

  // Get volume indicator
  const getVolumeIndicator = () => {
    if (volumeLevel === 0) return '🔇'
    if (volumeLevel < 0.3) return '🔈'
    if (volumeLevel < 0.7) return '🔉'
    return '🔊'
  }

  return (
    <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold flex items-center gap-2">
          📞 Voice Assistant Call
        </h3>
        <div className={`text-sm font-medium ${getStatusColor()}`}>
          {callStatus.status.charAt(0).toUpperCase() + callStatus.status.slice(1)}
          {callStatus.isActive && ` • ${formatDuration(callStatus.duration)}`}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          ❌ {error}
        </div>
      )}

      {/* Call Controls */}
      <div className="flex flex-wrap gap-3 mb-6">
        {!callStatus.isActive ? (
          <button
            onClick={startCall}
            disabled={isLoading || !vapi}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:opacity-50 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Connecting...
              </>
            ) : (
              <>
                📞 Start Voice Call
              </>
            )}
          </button>
        ) : (
          <>
            <button
              onClick={stopCall}
              className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              📞❌ End Call
            </button>
            <button
              onClick={toggleMute}
              className={`${
                callStatus.isMuted 
                  ? 'bg-yellow-600 hover:bg-yellow-700' 
                  : 'bg-blue-600 hover:bg-blue-700'
              } px-4 py-3 rounded-lg font-medium transition-colors flex items-center gap-2`}
            >
              {callStatus.isMuted ? '🔇 Unmute' : '🎤 Mute'}
            </button>
          </>
        )}
      </div>

      {/* Volume Level Indicator */}
      {callStatus.isActive && (
        <div className="mb-4 p-3 bg-white/5 rounded-lg">
          <div className="flex items-center gap-2 text-sm">
            <span>{getVolumeIndicator()}</span>
            <span className="text-gray-400">Volume:</span>
            <div className="flex-1 bg-gray-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-100"
                style={{ width: `${volumeLevel * 100}%` }}
              ></div>
            </div>
            <span className="text-sm">{Math.round(volumeLevel * 100)}%</span>
          </div>
        </div>
      )}

      {/* Live Transcript */}
      {transcript.length > 0 && (
        <div className="mt-6">
          <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
            📝 Live Transcript
          </h4>
          <div className="max-h-64 overflow-y-auto bg-black/20 rounded-lg p-4 space-y-2">
            {transcript.map((entry, index) => (
              <div key={index} className="text-sm">
                <span className={`font-medium ${
                  entry.role === 'user' ? 'text-blue-400' : 'text-green-400'
                }`}>
                  {entry.role === 'user' ? '👤 You' : '🤖 Assistant'}:
                </span>
                <span className="ml-2 text-gray-200">{entry.content}</span>
                <div className="text-xs text-gray-500 ml-2">
                  {entry.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      {!callStatus.isActive && !error && (
        <div className="text-sm text-gray-400 bg-white/5 rounded-lg p-4">
          <h4 className="font-medium mb-2">💡 How to use:</h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Click "Start Voice Call" to begin speaking with the AI assistant</li>
            <li>The assistant can help with financial analysis and general questions</li>
            <li>Try saying: "I need a financial analysis of Apple for credit risk"</li>
            <li>Use the mute button to control your microphone during the call</li>
          </ul>
        </div>
      )}
    </div>
  )
}

export default VoiceCall 