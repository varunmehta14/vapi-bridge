'use client'

import React, { useState } from 'react'

interface ServiceSelectorProps {
  onServiceChange: (service: string, port: number, configPath: string) => void
}

const ServiceSelector: React.FC<ServiceSelectorProps> = ({ onServiceChange }) => {
  const [selectedService, setSelectedService] = useState('dynamic')

  const services = [
    {
      id: 'dynamic',
      name: 'Dynamic Voice Agent System',
      description: 'Create unlimited voice agents with custom capabilities',
      port: 8000,
      configPath: '/config/yaml',
      status: '🤖 Voice Agents',
      color: 'bg-indigo-600'
    },
    {
      id: 'tesseract',
      name: 'Tesseract Engine',
      description: 'Workflow automation and command processing',
      port: 8081,
      configPath: '/config/yaml',
      status: '🔧 Workflow Engine',
      color: 'bg-blue-600'
    },
    {
      id: 'langgraph',
      name: 'LangGraph Research Assistant',
      description: 'AI-powered research and content generation',
      port: 8082,
      configPath: '/admin/database',
      status: '🔬 Research & Content',
      color: 'bg-green-600'
    }
  ]

  const handleServiceSelect = (service: any) => {
    setSelectedService(service.id)
    onServiceChange(service.id, service.port, service.configPath)
  }

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-white mb-4">Select AI Service Backend</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {services.map((service) => (
          <div
            key={service.id}
            onClick={() => handleServiceSelect(service)}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
              selectedService === service.id
                ? `${service.color} border-white/50 shadow-lg`
                : 'bg-black/20 border-white/20 hover:border-white/40'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-white">{service.name}</h4>
              <span className="text-sm text-gray-300">{service.status}</span>
            </div>
            <p className="text-sm text-gray-300 mb-2">{service.description}</p>
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>Port: {service.port}</span>
              <span className={selectedService === service.id ? 'text-white' : ''}>
                {selectedService === service.id ? '✅ Selected' : 'Click to select'}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
        <h4 className="text-blue-300 font-medium mb-2">🎯 Service Selection Guide:</h4>
        <div className="text-blue-200 text-sm space-y-1">
          <div>• <strong>Dynamic Voice Agent System:</strong> Create unlimited custom voice assistants with any tools you need</div>
          <div>• <strong>Tesseract Engine:</strong> Use pre-built workflow automation and business process tools</div>
          <div>• <strong>LangGraph Research:</strong> Access advanced research and content generation capabilities</div>
        </div>
        <div className="mt-2 text-xs text-blue-300">
          💡 Choose the backend that best matches your voice agent requirements. You can switch between services anytime.
        </div>
      </div>
    </div>
  )
}

export default ServiceSelector 