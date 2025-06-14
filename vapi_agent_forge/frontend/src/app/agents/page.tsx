'use client'

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import ResponseRenderer from '@/components/ResponseRenderer'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

export default function AgentsPage() {
  const [yamlConfig, setYamlConfig] = useState(`# Agent Configuration
assistant:
  name: "Tesseract Command Assistant"
  model:
    provider: "openai"
    model: "gpt-4o-mini"
    system_prompt_template: |
      You are a specialized AI assistant for the Tesseract system. Your goal is to accurately trigger the correct tool based on the user's request.

      CRITICAL RULES:
      1. If the user's request clearly matches a specific workflow tool like 'triggerFinancialAnalysisWorkflow', ask for any missing parameters and then call that tool.
      2. For ALL OTHER requests, including simple questions, greetings, or ambiguous commands, you MUST use the 'processGeneralRequest' tool. Do not try to answer yourself.
      3. The user's ID is {user_id}.

      Example 1: User says "I need a financial analysis of Tesla". You should ask clarifying questions for 'analysis_type', then call 'triggerFinancialAnalysisWorkflow'.
      Example 2: User says "What's the weather?" or "Hello there". You MUST call 'processGeneralRequest'.
  voice: 
    provider: "playht"
    voiceId: "jennifer-playht"
  firstMessage: "Tesseract system online. How can I assist you?"

tools:
  # TOOL 1: For specific, known workflows
  - name: "triggerFinancialAnalysisWorkflow"
    description: "Use this specific tool to run a multi-step financial analysis on a company. Requires the company name and the type of analysis."
    parameters:
      type: "object"
      properties:
        user_id:
          type: "string"
          description: "The user's unique ID."
        company_name:
          type: "string"
          description: "The name of the company to analyze, e.g., 'Tesla Inc'."
        analysis_type:
          type: "string"
          description: "The type of analysis to run, e.g., 'credit_risk', 'standard_review'."
      required: ["user_id", "company_name", "analysis_type"]
    action:
      type: "api_call"
      method: "POST"
      url: "http://localhost:8081/run_workflow/financial_analysis/{user_id}"
      json_body:
        input_params:
          company_name: "{company_name}"
          analysis_type: "{analysis_type}"
      response_template: "Workflow initiated. The Job ID is {job_id}."

  # TOOL 2: The general-purpose fallback
  - name: "processGeneralRequest"
    description: "A general-purpose tool for all other requests, simple questions, or ambiguous commands that do not fit a specific workflow."
    parameters:
      type: "object"
      properties:
        user_id:
          type: "string"
          description: "The user's unique ID."
        user_input:
          type: "string"
          description: "The user's full, verbatim request."
      required: ["user_id", "user_input"]
    action:
      type: "api_call"
      method: "POST"
      url: "http://localhost:8081/receive_user_input/{user_id}"
      json_body:
        user_input: "{user_input}"
      response_path: "response"
`)

  const [testResult, setTestResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'editor' | 'test'>('editor')

  const handleSave = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: yamlConfig })
      })
      
      const result = await response.json()
      setTestResult({
        success: response.ok,
        message: response.ok ? 'Agent saved successfully!' : 'Failed to save agent',
        data: result
      })
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
      const response = await fetch('/api/agents/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: yamlConfig })
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
        message: 'Error testing configuration',
        error: error instanceof Error ? error.message : 'Unknown error',
        validation: true
      })
    }
    setIsLoading(false)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Agent Builder</h1>
        <p className="text-gray-300">Create and configure your AI agents using YAML</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-6">
        <button
          onClick={() => setActiveTab('editor')}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            activeTab === 'editor'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          YAML Editor
        </button>
        <button
          onClick={() => setActiveTab('test')}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            activeTab === 'test'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-black/20 text-gray-300 hover:bg-black/30'
          }`}
        >
          Test Results
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Editor Section */}
        {activeTab === 'editor' && (
          <div className="lg:col-span-2">
            <div className="bg-black/20 backdrop-blur-md rounded-lg p-6 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Agent Configuration</h2>
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
                  onChange={(value) => setYamlConfig(value || '')}
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
            </div>
          </div>
        )}

        {/* Test Results Section */}
        {activeTab === 'test' && testResult && (
          <div className="lg:col-span-2">
            <div className="space-y-6">
              <ResponseRenderer 
                data={testResult} 
                title="Configuration Test Results"
              />
              
              {testResult.data && (
                <ResponseRenderer 
                  data={testResult.data} 
                  title="Detailed Response Data"
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Real-time status indicator */}
      <div className="fixed bottom-6 right-6">
        <div className="bg-black/40 backdrop-blur-md rounded-full px-4 py-2 border border-white/10">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
            <span className="text-sm text-white">
              {isLoading ? 'Processing...' : 'Ready'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
} 