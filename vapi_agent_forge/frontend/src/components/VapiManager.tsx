'use client'

import React, { useState, useEffect } from 'react'

interface VapiManagerProps {
  onClose: () => void
}

interface VapiAssistant {
  id: string
  name: string
  createdAt: string
  updatedAt: string
}

interface VapiTool {
  id: string
  function: {
    name: string
    description: string
  }
  createdAt: string
}

const VapiManager: React.FC<VapiManagerProps> = ({ onClose }) => {
  const [assistants, setAssistants] = useState<VapiAssistant[]>([])
  const [tools, setTools] = useState<VapiTool[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'assistants' | 'tools'>('assistants')
  
  // Create assistant form
  const [newAssistantUserId, setNewAssistantUserId] = useState<string>('demo_user')
  const [isCreating, setIsCreating] = useState<boolean>(false)

  useEffect(() => {
    if (activeTab === 'assistants') {
      loadAssistants()
    } else {
      loadTools()
    }
  }, [activeTab])

  const loadAssistants = async () => {
    setIsLoading(true)
    setError('')
    try {
      const response = await fetch('http://localhost:8000/vapi/assistants')
      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        setAssistants(data.assistants || [])
      } else {
        setError(data.detail || 'Failed to load assistants')
      }
    } catch (err) {
      setError(`Error loading assistants: ${(err as Error).message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const loadTools = async () => {
    setIsLoading(true)
    setError('')
    try {
      const response = await fetch('http://localhost:8000/vapi/tools')
      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        setTools(data.tools || [])
      } else {
        setError(data.detail || 'Failed to load tools')
      }
    } catch (err) {
      setError(`Error loading tools: ${(err as Error).message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const createAssistant = async () => {
    if (!newAssistantUserId.trim()) {
      setError('Please enter a user ID')
      return
    }

    setIsCreating(true)
    setError('')
    setSuccess('')
    
    try {
      const response = await fetch('http://localhost:8000/vapi/assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: newAssistantUserId })
      })
      
      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        setSuccess(`✅ Assistant created successfully! ID: ${data.assistant_id}`)
        setNewAssistantUserId('demo_user')
        loadAssistants() // Refresh the list
      } else {
        setError(data.detail || 'Failed to create assistant')
      }
    } catch (err) {
      setError(`Error creating assistant: ${(err as Error).message}`)
    } finally {
      setIsCreating(false)
    }
  }

  const deleteAssistant = async (assistantId: string) => {
    if (!confirm('Are you sure you want to delete this assistant?')) {
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/vapi/assistant/${assistantId}`, {
        method: 'DELETE'
      })
      
      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        setSuccess('Assistant deleted successfully')
        loadAssistants() // Refresh the list
      } else {
        setError(data.detail || 'Failed to delete assistant')
      }
    } catch (err) {
      setError(`Error deleting assistant: ${(err as Error).message}`)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/10 backdrop-blur rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden border border-white/20">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/20">
          <h2 className="text-2xl font-bold text-white">
            🤖 Vapi Assistant Manager
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-white/20">
          <button
            onClick={() => setActiveTab('assistants')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'assistants'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            👤 Assistants
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'tools'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            🛠️ Tools
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Error/Success Messages */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-300">❌ {error}</p>
            </div>
          )}
          
          {success && (
            <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4">
              <p className="text-green-300">{success}</p>
            </div>
          )}

          {activeTab === 'assistants' && (
            <div className="space-y-6">
              {/* Create New Assistant */}
              <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-300 mb-4">➕ Create New Assistant</h3>
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-white mb-2">
                      User ID:
                    </label>
                    <input
                      type="text"
                      value={newAssistantUserId}
                      onChange={(e) => setNewAssistantUserId(e.target.value)}
                      className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-gray-400"
                      placeholder="Enter user ID (e.g., demo_user)"
                    />
                  </div>
                  <button
                    onClick={createAssistant}
                    disabled={isCreating}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-2 rounded-lg text-white font-medium transition-colors"
                  >
                    {isCreating ? 'Creating...' : '🚀 Create Assistant'}
                  </button>
                </div>
              </div>

              {/* Assistants List */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">📋 Existing Assistants</h3>
                {isLoading ? (
                  <div className="bg-white/5 rounded-lg p-8 text-center">
                    <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full mx-auto mb-2"></div>
                    <p className="text-gray-300">Loading assistants...</p>
                  </div>
                ) : assistants.length === 0 ? (
                  <div className="bg-white/5 rounded-lg p-8 text-center">
                    <p className="text-gray-300">No assistants found. Create one above!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {assistants.map((assistant) => (
                      <div key={assistant.id} className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="text-lg font-semibold text-white">{assistant.name}</h4>
                            <p className="text-gray-300 text-sm">ID: {assistant.id}</p>
                            <p className="text-gray-400 text-xs">Created: {formatDate(assistant.createdAt)}</p>
                          </div>
                          <div className="space-x-2">
                            <button
                              onClick={() => navigator.clipboard.writeText(assistant.id)}
                              className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm text-white transition-colors"
                            >
                              📋 Copy ID
                            </button>
                            <button
                              onClick={() => deleteAssistant(assistant.id)}
                              className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm text-white transition-colors"
                            >
                              🗑️ Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'tools' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">🔧 Vapi Tools</h3>
                {isLoading ? (
                  <div className="bg-white/5 rounded-lg p-8 text-center">
                    <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full mx-auto mb-2"></div>
                    <p className="text-gray-300">Loading tools...</p>
                  </div>
                ) : tools.length === 0 ? (
                  <div className="bg-white/5 rounded-lg p-8 text-center">
                    <p className="text-gray-300">No tools found. Create an assistant to generate tools!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tools.map((tool) => (
                      <div key={tool.id} className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="text-lg font-semibold text-white">{tool.function.name}</h4>
                            <p className="text-gray-300 text-sm">{tool.function.description}</p>
                            <p className="text-gray-400 text-xs">ID: {tool.id}</p>
                            <p className="text-gray-400 text-xs">Created: {formatDate(tool.createdAt)}</p>
                          </div>
                          <button
                            onClick={() => navigator.clipboard.writeText(tool.id)}
                            className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm text-white transition-colors"
                          >
                            📋 Copy ID
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/20 p-4 bg-white/5">
          <div className="flex justify-between items-center">
            <p className="text-gray-400 text-sm">
              💡 Make sure VAPI_API_KEY and PUBLIC_SERVER_URL are properly configured
            </p>
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg text-white font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VapiManager 