'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Navigation from '../../components/Navigation'

interface User {
  id: number
  username: string
}

interface VoiceAgent {
  id: number
  name: string
  agent_type: string
}

interface Interaction {
  id: number
  type: string
  content: string
  timestamp: string
  agent_name: string
  voice_agent_id: number
}

const InteractionsPage: React.FC = () => {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [interactions, setInteractions] = useState<Interaction[]>([])
  const [voiceAgents, setVoiceAgents] = useState<VoiceAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState<string>('all')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [limit] = useState(50)

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (!userData) {
      router.push('/login')
      return
    }
    
    const parsedUser = JSON.parse(userData)
    setUser(parsedUser)
    loadUserData(parsedUser.id)
  }, [router])

  const loadUserData = async (userId: number) => {
    try {
      setIsLoading(true)
      
      // Load voice agents
      const agentsResponse = await fetch(`http://localhost:8000/users/${userId}/voice-agents`)
      const agentsData = await agentsResponse.json()
      if (agentsData.status === 'success') {
        setVoiceAgents(agentsData.voice_agents)
      }

      // Load interactions
      const interactionsResponse = await fetch(`http://localhost:8000/users/${userId}/interactions?limit=${limit * currentPage}`)
      const interactionsData = await interactionsResponse.json()
      if (interactionsData.status === 'success') {
        setInteractions(interactionsData.interactions)
      }
      
    } catch (error) {
      console.error('Failed to load user data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    router.push('/login')
  }

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case 'call_started': return '📞'
      case 'call_ended': return '📵'
      case 'user_message': return '👤'
      case 'function_call': return '🔧'
      case 'agent_created': return '✨'
      case 'agent_deleted': return '🗑️'
      case 'error': return '❌'
      default: return '💬'
    }
  }

  const getInteractionColor = (type: string) => {
    switch (type) {
      case 'call_started': return 'text-green-400'
      case 'call_ended': return 'text-red-400'
      case 'user_message': return 'text-blue-400'
      case 'function_call': return 'text-yellow-400'
      case 'agent_created': return 'text-purple-400'
      case 'agent_deleted': return 'text-red-400'
      case 'error': return 'text-red-500'
      default: return 'text-gray-400'
    }
  }

  const getInteractionBorder = (type: string) => {
    switch (type) {
      case 'call_started': return 'border-l-green-400'
      case 'call_ended': return 'border-l-red-400'
      case 'user_message': return 'border-l-blue-400'
      case 'function_call': return 'border-l-yellow-400'
      case 'agent_created': return 'border-l-purple-400'
      case 'agent_deleted': return 'border-l-red-400'
      case 'error': return 'border-l-red-500'
      default: return 'border-l-gray-400'
    }
  }

  // Filter interactions based on selected filters and search
  const filteredInteractions = interactions.filter(interaction => {
    const matchesAgent = selectedAgent === 'all' || interaction.voice_agent_id === parseInt(selectedAgent)
    const matchesType = selectedType === 'all' || interaction.type === selectedType
    const matchesSearch = searchQuery === '' || 
      interaction.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      interaction.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      interaction.agent_name?.toLowerCase().includes(searchQuery.toLowerCase())
    
    return matchesAgent && matchesType && matchesSearch
  })

  // Get unique interaction types for filter
  const interactionTypes = [...new Set(interactions.map(i => i.type))]

  // Group interactions by date
  const groupedInteractions = filteredInteractions.reduce((groups, interaction) => {
    const date = new Date(interaction.timestamp).toDateString()
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(interaction)
    return groups
  }, {} as Record<string, Interaction[]>)

  const exportInteractions = () => {
    const csv = [
      ['Timestamp', 'Type', 'Agent', 'Content'],
      ...filteredInteractions.map(i => [
        i.timestamp,
        i.type,
        i.agent_name || 'Unknown',
        i.content.replace(/"/g, '""')
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `interactions-${user?.username}-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading interactions...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <Navigation currentPage="interactions" user={user} />

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
            <div className="text-2xl font-bold text-blue-400">{interactions.length}</div>
            <div className="text-sm text-gray-300">Total Interactions</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
            <div className="text-2xl font-bold text-green-400">
              {interactions.filter(i => i.type === 'user_message').length}
            </div>
            <div className="text-sm text-gray-300">Messages</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
            <div className="text-2xl font-bold text-yellow-400">
              {interactions.filter(i => i.type === 'function_call').length}
            </div>
            <div className="text-sm text-gray-300">Function Calls</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
            <div className="text-2xl font-bold text-purple-400">{voiceAgents.length}</div>
            <div className="text-sm text-gray-300">Voice Agents</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20 mb-8">
          <h2 className="text-xl font-semibold mb-4">🔍 Filters</h2>
          <div className="grid md:grid-cols-4 gap-4">
            {/* Agent Filter */}
            <div>
              <label className="block text-sm font-medium mb-2">Voice Agent</label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all" className="bg-gray-800">All Agents</option>
                {voiceAgents.map((agent) => (
                  <option key={agent.id} value={agent.id} className="bg-gray-800">
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-sm font-medium mb-2">Interaction Type</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all" className="bg-gray-800">All Types</option>
                {interactionTypes.map((type) => (
                  <option key={type} value={type} className="bg-gray-800">
                    {getInteractionIcon(type)} {type.replace('_', ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* Search */}
            <div>
              <label className="block text-sm font-medium mb-2">Search</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search content..."
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Export */}
            <div>
              <label className="block text-sm font-medium mb-2">Export</label>
              <button
                onClick={exportInteractions}
                className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                📥 Download CSV
              </button>
            </div>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-gray-300">
            Showing {filteredInteractions.length} of {interactions.length} interactions
          </p>
        </div>

        {/* Interactions List */}
        {Object.keys(groupedInteractions).length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedInteractions)
              .sort(([a], [b]) => new Date(b).getTime() - new Date(a).getTime())
              .map(([date, dayInteractions]) => (
                <div key={date} className="bg-white/10 backdrop-blur rounded-lg border border-white/20">
                  <div className="px-6 py-4 border-b border-white/10">
                    <h3 className="text-lg font-semibold">📅 {date}</h3>
                    <p className="text-sm text-gray-400">{dayInteractions.length} interactions</p>
                  </div>
                  <div className="p-6">
                    <div className="space-y-4">
                      {dayInteractions
                        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                        .map((interaction, index) => (
                          <div
                            key={`${interaction.id}-${index}`}
                            className={`border-l-4 ${getInteractionBorder(interaction.type)} bg-white/5 rounded-r-lg p-4`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-start gap-3 flex-1">
                                <span className="text-xl">{getInteractionIcon(interaction.type)}</span>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`font-medium ${getInteractionColor(interaction.type)}`}>
                                      {interaction.type.replace('_', ' ').toUpperCase()}
                                    </span>
                                    {interaction.agent_name && (
                                      <span className="px-2 py-1 bg-blue-600 text-xs rounded text-white">
                                        {interaction.agent_name}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-white mb-2">{interaction.content}</p>
                                  <div className="text-xs text-gray-400">
                                    {new Date(interaction.timestamp).toLocaleString()}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white/5 rounded-lg">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">No Interactions Found</h3>
            <p className="text-gray-400 mb-6">
              {interactions.length === 0 
                ? "Start using voice agents to see interactions here" 
                : "Try adjusting your filters to see more results"}
            </p>
            <button
              onClick={() => router.push('/')}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              🎤 Start Voice Call
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default InteractionsPage 