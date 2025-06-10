'use client'

import React, { useState, useEffect, useCallback } from 'react'
import ConfigEditor from './ConfigEditor'
import VapiManager from './VapiManager'

interface ServiceStatus {
  online: boolean
  message?: string
  error?: string
}

interface ToolTestParams {
  [key: string]: string | number
}

interface ToolTestResponse {
  tool_name: string
  parameters: ToolTestParams
  result?: string
  error?: string
  status: string
}

interface SystemStatus {
  tesseract_engine: ServiceStatus
  vapi_forge: ServiceStatus
  environment: {
    public_server_url: string
    vapi_api_key_set: boolean
    ngrok_active: boolean
  }
  configuration: {
    tools_count: number
    assistant_configured: boolean
  }
}

const Dashboard: React.FC = () => {
  const [tesseractStatus, setTesseractStatus] = useState<ServiceStatus>({ online: false })
  const [forgeStatus, setForgeStatus] = useState<ServiceStatus>({ online: false })
  const [ngrokStatus, setNgrokStatus] = useState<ServiceStatus>({ online: false })
  const [selectedTool, setSelectedTool] = useState<string | null>(null)
  const [testResponse, setTestResponse] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  
  // Modal states
  const [showConfigEditor, setShowConfigEditor] = useState<boolean>(false)
  const [showVapiManager, setShowVapiManager] = useState<boolean>(false)
  
  // Form state for financial analysis
  const [financialParams, setFinancialParams] = useState({
    userId: 'test_user_123',
    companyName: 'Tesla Inc',
    analysisType: 'standard_review'
  })
  
  // Form state for general request
  const [generalParams, setGeneralParams] = useState({
    userId: 'test_user_123',
    userInput: 'Hello there! What can you help me with?'
  })

  const checkSystemStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/status')
      const data = await response.json()
      
      if (data.status === 'success') {
        setSystemStatus(data)
        setTesseractStatus(data.tesseract_engine)
        setForgeStatus(data.vapi_forge)
        setNgrokStatus({
          online: data.environment.ngrok_active,
          message: data.environment.ngrok_active 
            ? data.environment.public_server_url 
            : 'Using localhost (ngrok not active)'
        })
      }
    } catch (error) {
      console.error('System status check failed:', error)
    }
  }, [])

  const checkTesseractStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8081/')
      const data = await response.json()
      setTesseractStatus({ online: true, message: data.message })
      console.log('Tesseract Engine:', data)
    } catch (error) {
      setTesseractStatus({ online: false, error: (error as Error).message })
      console.error('Tesseract Engine offline:', error)
    }
  }, [])

  const checkForgeStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/')
      const data = await response.json()
      setForgeStatus({ online: true, message: data.message })
      console.log('Vapi Forge:', data)
    } catch (error) {
      setForgeStatus({ online: false, error: (error as Error).message })
      console.error('Vapi Forge offline:', error)
    }
  }, [])

  const checkNgrokStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/')
      const data = await response.json()
      const publicUrl = data.public_url
      const isNgrokActive = !publicUrl.includes('localhost')
      setNgrokStatus({ 
        online: isNgrokActive, 
        message: isNgrokActive ? publicUrl : 'Using localhost (ngrok not active)' 
      })
      console.log('Public URL:', publicUrl)
    } catch (error) {
      setNgrokStatus({ online: false, error: (error as Error).message })
      console.error('Cannot check ngrok status:', error)
    }
  }, [])

  const testFinancialTool = async () => {
    setIsLoading(true)
    setTestResponse('Testing financial analysis tool...')
    
    try {
      const response = await fetch('http://localhost:8000/test-tool/triggerFinancialAnalysisWorkflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: financialParams.userId,
          company_name: financialParams.companyName,
          analysis_type: financialParams.analysisType
        })
      })
      
      const data: ToolTestResponse = await response.json()
      setTestResponse(JSON.stringify(data, null, 2))
    } catch (error) {
      setTestResponse(`Error: ${(error as Error).message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const testGeneralTool = async () => {
    setIsLoading(true)
    setTestResponse('Testing general request processing...')
    
    try {
      const response = await fetch('http://localhost:8000/test-tool/processGeneralRequest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: generalParams.userId,
          user_input: generalParams.userInput
        })
      })
      
      const data: ToolTestResponse = await response.json()
      setTestResponse(JSON.stringify(data, null, 2))
    } catch (error) {
      setTestResponse(`Error: ${(error as Error).message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const refreshAllStatuses = useCallback(() => {
    checkSystemStatus()
    checkTesseractStatus()
    checkForgeStatus()
    checkNgrokStatus()
  }, [checkSystemStatus, checkTesseractStatus, checkForgeStatus, checkNgrokStatus])

  useEffect(() => {
    // Check status on component mount
    const timer = setTimeout(() => {
      refreshAllStatuses()
    }, 1000)

    return () => clearTimeout(timer)
  }, [refreshAllStatuses])

  const StatusIndicator: React.FC<{ status: ServiceStatus; name: string }> = ({ status, name }) => (
    <div className={`w-4 h-4 rounded-full ${status.online ? 'bg-green-500' : 'bg-red-500'}`} />
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            🤖 Tesseract + Vapi Control Panel
          </h1>
          <p className="text-lg text-gray-300">
            Voice-Activated Workflow Automation System
          </p>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-4 justify-center">
            <button
              onClick={() => setShowConfigEditor(true)}
              className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              📝 Edit YAML Config
            </button>
            <button
              onClick={() => setShowVapiManager(true)}
              className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              🤖 Manage Vapi Assistants
            </button>
            <button
              onClick={refreshAllStatuses}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              🔄 Refresh Status
            </button>
          </div>
        </div>

        {/* System Status */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 flex items-center">
            📊 System Status
            {systemStatus && (
              <span className="ml-4 text-sm text-gray-400">
                ({systemStatus.configuration.tools_count} tools configured)
              </span>
            )}
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
              <div className="flex items-center justify-between mb-4">
                <StatusIndicator status={tesseractStatus} name="Tesseract Engine" />
                <h3 className="text-xl font-semibold">Tesseract Engine</h3>
              </div>
              <p className="text-gray-300 mb-4">Port 8081</p>
              <button
                onClick={checkTesseractStatus}
                className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Check Status
              </button>
              {tesseractStatus.message && (
                <p className="mt-2 text-green-400 text-sm">{tesseractStatus.message}</p>
              )}
              {tesseractStatus.error && (
                <p className="mt-2 text-red-400 text-sm">{tesseractStatus.error}</p>
              )}
            </div>

            <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
              <div className="flex items-center justify-between mb-4">
                <StatusIndicator status={forgeStatus} name="Vapi Forge" />
                <h3 className="text-xl font-semibold">Vapi Forge</h3>
              </div>
              <p className="text-gray-300 mb-4">Port 8000</p>
              <button
                onClick={checkForgeStatus}
                className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Check Status
              </button>
              {forgeStatus.message && (
                <p className="mt-2 text-green-400 text-sm">{forgeStatus.message}</p>
              )}
              {forgeStatus.error && (
                <p className="mt-2 text-red-400 text-sm">{forgeStatus.error}</p>
              )}
            </div>

            <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
              <div className="flex items-center justify-between mb-4">
                <StatusIndicator status={ngrokStatus} name="Ngrok Tunnel" />
                <h3 className="text-xl font-semibold">Ngrok Tunnel</h3>
              </div>
              <p className="text-gray-300 mb-4">Public URL</p>
              <button
                onClick={checkNgrokStatus}
                className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Check Status
              </button>
              {ngrokStatus.message && (
                <p className="mt-2 text-green-400 text-sm break-all">{ngrokStatus.message}</p>
              )}
              {ngrokStatus.error && (
                <p className="mt-2 text-red-400 text-sm">{ngrokStatus.error}</p>
              )}
            </div>
          </div>
          
          {/* Environment Info */}
          {systemStatus && (
            <div className="mt-6 bg-white/5 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">🔧 Environment Configuration</h3>
              <div className="grid md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">VAPI API Key:</span>
                  <span className={`ml-2 ${systemStatus.environment.vapi_api_key_set ? 'text-green-400' : 'text-red-400'}`}>
                    {systemStatus.environment.vapi_api_key_set ? '✅ Set' : '❌ Not Set'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Ngrok Active:</span>
                  <span className={`ml-2 ${systemStatus.environment.ngrok_active ? 'text-green-400' : 'text-yellow-400'}`}>
                    {systemStatus.environment.ngrok_active ? '✅ Active' : '⚠️ Local Only'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Assistant Config:</span>
                  <span className={`ml-2 ${systemStatus.configuration.assistant_configured ? 'text-green-400' : 'text-red-400'}`}>
                    {systemStatus.configuration.assistant_configured ? '✅ Ready' : '❌ Missing'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Available Tools */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 flex items-center">
            🛠️ Available Tools
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
              <h3 className="text-xl font-semibold mb-3">triggerFinancialAnalysisWorkflow</h3>
              <p className="text-gray-300 mb-4">
                Runs comprehensive financial analysis on companies with customizable analysis types.
              </p>
              <button
                onClick={() => setSelectedTool('financial')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedTool === 'financial' 
                    ? 'bg-purple-600 hover:bg-purple-700' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                Test Tool
              </button>
            </div>

            <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
              <h3 className="text-xl font-semibold mb-3">processGeneralRequest</h3>
              <p className="text-gray-300 mb-4">
                Handles general queries, greetings, and ambiguous commands with intelligent routing.
              </p>
              <button
                onClick={() => setSelectedTool('general')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedTool === 'general' 
                    ? 'bg-purple-600 hover:bg-purple-700' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                Test Tool
              </button>
            </div>
          </div>
        </div>

        {/* Test Interface */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 flex items-center">
            🧪 Test Interface
          </h2>
          <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
            {!selectedTool && (
              <p className="text-center text-gray-400 py-8">
                Select a tool above to start testing
              </p>
            )}

            {selectedTool === 'financial' && (
              <div>
                <h3 className="text-xl font-semibold mb-4">Test Financial Analysis Workflow</h3>
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">User ID:</label>
                    <input
                      type="text"
                      value={financialParams.userId}
                      onChange={(e) => setFinancialParams(prev => ({...prev, userId: e.target.value}))}
                      className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-gray-400"
                      placeholder="Enter user ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Company Name:</label>
                    <input
                      type="text"
                      value={financialParams.companyName}
                      onChange={(e) => setFinancialParams(prev => ({...prev, companyName: e.target.value}))}
                      className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-gray-400"
                      placeholder="Enter company name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Analysis Type:</label>
                    <select
                      value={financialParams.analysisType}
                      onChange={(e) => setFinancialParams(prev => ({...prev, analysisType: e.target.value}))}
                      className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white"
                    >
                      <option value="standard_review">Standard Review</option>
                      <option value="credit_risk">Credit Risk Analysis</option>
                    </select>
                  </div>
                </div>
                <button
                  onClick={testFinancialTool}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  {isLoading ? 'Executing...' : 'Execute Test'}
                </button>
              </div>
            )}

            {selectedTool === 'general' && (
              <div>
                <h3 className="text-xl font-semibold mb-4">Test General Request Processing</h3>
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">User ID:</label>
                    <input
                      type="text"
                      value={generalParams.userId}
                      onChange={(e) => setGeneralParams(prev => ({...prev, userId: e.target.value}))}
                      className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-gray-400"
                      placeholder="Enter user ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">User Input:</label>
                    <textarea
                      value={generalParams.userInput}
                      onChange={(e) => setGeneralParams(prev => ({...prev, userInput: e.target.value}))}
                      className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-gray-400"
                      placeholder="Enter your message..."
                      rows={4}
                    />
                  </div>
                </div>
                <button
                  onClick={testGeneralTool}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-6 py-3 rounded-lg text-white font-medium transition-colors"
                >
                  {isLoading ? 'Executing...' : 'Execute Test'}
                </button>
              </div>
            )}

            {testResponse && (
              <div className="mt-6">
                <h4 className="text-lg font-semibold mb-3">Response:</h4>
                <pre className="bg-black/30 p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
                  {testResponse}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showConfigEditor && (
        <ConfigEditor onClose={() => setShowConfigEditor(false)} />
      )}
      
      {showVapiManager && (
        <VapiManager onClose={() => setShowVapiManager(false)} />
      )}
    </div>
  )
}

export default Dashboard 