'use client'

import React, { useState, useEffect } from 'react'

interface ConfigEditorProps {
  onClose: () => void
}

interface ConfigData {
  assistant: {
    name: string
    model: {
      provider: string
      model: string
      system_prompt_template: string
    }
    voice: {
      provider: string
      voiceId: string
    }
    firstMessage: string
  }
  tools: Array<{
    name: string
    description: string
    parameters: object
    action: object
  }>
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ onClose }) => {
  const [yamlContent, setYamlContent] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')

  useEffect(() => {
    loadCurrentConfig()
  }, [])

  const loadCurrentConfig = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/config/yaml')
      const data = await response.json()
      if (data.status === 'success') {
        setYamlContent(data.yaml)
      } else {
        setError('Failed to load configuration')
      }
    } catch (err) {
      setError(`Error loading configuration: ${(err as Error).message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const saveConfiguration = async () => {
    setIsSaving(true)
    setError('')
    setSuccess('')
    
    try {
      const response = await fetch('http://localhost:8000/config/yaml', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ yaml: yamlContent })
      })
      
      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        setSuccess('Configuration updated successfully!')
        setTimeout(() => {
          onClose()
        }, 2000)
      } else {
        setError(data.detail || 'Failed to save configuration')
      }
    } catch (err) {
      setError(`Error saving configuration: ${(err as Error).message}`)
    } finally {
      setIsSaving(false)
    }
  }

  const resetToDefault = () => {
    loadCurrentConfig()
    setError('')
    setSuccess('')
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/10 backdrop-blur rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden border border-white/20">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/20">
          <h2 className="text-2xl font-bold text-white">
            📝 YAML Configuration Editor
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Instructions */}
          <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-blue-300 mb-2">📖 Instructions</h3>
            <ul className="text-blue-200 text-sm space-y-1">
              <li>• Edit the YAML configuration below to customize your assistant and tools</li>
              <li>• The configuration will be validated before saving</li>
              <li>• Changes will reload the tool executor automatically</li>
              <li>• Make sure to maintain proper YAML syntax</li>
            </ul>
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-300">❌ {error}</p>
            </div>
          )}
          
          {success && (
            <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4">
              <p className="text-green-300">✅ {success}</p>
            </div>
          )}

          {/* YAML Editor */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-white">
              YAML Configuration:
            </label>
            {isLoading ? (
              <div className="bg-white/5 rounded-lg p-8 text-center">
                <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full mx-auto mb-2"></div>
                <p className="text-gray-300">Loading configuration...</p>
              </div>
            ) : (
              <textarea
                value={yamlContent}
                onChange={(e) => setYamlContent(e.target.value)}
                className="w-full h-96 px-4 py-3 bg-black/50 border border-white/30 rounded-lg text-white font-mono text-sm resize-none"
                placeholder="Enter your YAML configuration here..."
                style={{ fontFamily: 'Monaco, Consolas, "Courier New", monospace' }}
              />
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between pt-4">
            <div className="space-x-3">
              <button
                onClick={resetToDefault}
                disabled={isLoading}
                className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-800 px-4 py-2 rounded-lg text-white font-medium transition-colors"
              >
                🔄 Reset
              </button>
            </div>
            <div className="space-x-3">
              <button
                onClick={onClose}
                className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg text-white font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={saveConfiguration}
                disabled={isSaving || isLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-2 rounded-lg text-white font-medium transition-colors"
              >
                {isSaving ? 'Saving...' : '💾 Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigEditor 