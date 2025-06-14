import React from 'react'

interface ResponseRendererProps {
  data: any
  title?: string
  className?: string
}

export default function ResponseRenderer({ data, title, className = '' }: ResponseRendererProps) {
  const renderContent = () => {
    if (data === null || data === undefined) {
      return <div className="text-gray-400 italic">No data</div>
    }

    // Handle string data
    if (typeof data === 'string') {
      try {
        // Try to parse as JSON
        const parsed = JSON.parse(data)
        return (
          <pre className="bg-gray-800 text-green-400 p-4 rounded-lg overflow-auto max-h-96 text-sm font-mono whitespace-pre-wrap">
            {JSON.stringify(parsed, null, 2)}
          </pre>
        )
      } catch {
        // If not JSON, render as plain text
        return (
          <div className="text-white whitespace-pre-wrap bg-gray-800 p-4 rounded-lg max-h-96 overflow-auto">
            {data}
          </div>
        )
      }
    }

    // Handle objects and arrays
    if (typeof data === 'object') {
      return (
        <pre className="bg-gray-800 text-green-400 p-4 rounded-lg overflow-auto max-h-96 text-sm font-mono whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      )
    }

    // Handle primitives (numbers, booleans, etc.)
    return (
      <div className="text-white bg-gray-800 p-4 rounded-lg">
        <span className="font-mono">{String(data)}</span>
      </div>
    )
  }

  const getStatusColor = () => {
    if (typeof data === 'object' && data !== null) {
      if (data.success === true) return 'border-green-500/50'
      if (data.success === false || data.error) return 'border-red-500/50'
    }
    return 'border-white/10'
  }

  return (
    <div className={`bg-black/20 backdrop-blur-md rounded-lg p-6 border ${getStatusColor()} ${className}`}>
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          {typeof data === 'object' && data !== null && (
            <div className="flex items-center space-x-2">
              {data.success === true && (
                <span className="px-2 py-1 bg-green-600 text-white text-xs rounded-full">SUCCESS</span>
              )}
              {(data.success === false || data.error) && (
                <span className="px-2 py-1 bg-red-600 text-white text-xs rounded-full">ERROR</span>
              )}
            </div>
          )}
        </div>
      )}
      {renderContent()}
    </div>
  )
} 