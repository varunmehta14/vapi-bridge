'use client'

import React from 'react'
import { useRouter } from 'next/navigation'

interface NavigationProps {
  currentPage?: 'dashboard' | 'interactions' | 'agents'
  user?: {
    id: number
    username: string
  } | null
}

const Navigation: React.FC<NavigationProps> = ({ currentPage = 'dashboard', user }) => {
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem('user')
    router.push('/login')
  }

  const navItems = [
    {
      key: 'dashboard',
      label: '🏠 Dashboard',
      path: '/',
      color: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      key: 'agents',
      label: '🤖 Agents',
      path: '/agents',
      color: 'bg-orange-600 hover:bg-orange-700'
    },
    {
      key: 'interactions',
      label: '📊 Interactions',
      path: '/interactions',
      color: 'bg-purple-600 hover:bg-purple-700'
    }
  ]

  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-4xl font-bold mb-2">🤖 Vapi Agent Forge</h1>
        <p className="text-gray-300">
          Welcome back, {user?.username}! 
          {currentPage === 'dashboard' && ' Your voice agent management dashboard.'}
          {currentPage === 'agents' && ' Create, configure and manage your voice agents.'}
          {currentPage === 'interactions' && ' View all your voice agent interactions.'}
        </p>
      </div>
      <div className="flex gap-4">
        {navItems
          .filter(item => item.key !== currentPage)
          .map(item => (
            <button
              key={item.key}
              onClick={() => router.push(item.path)}
              className={`px-4 py-2 ${item.color} text-white rounded-lg transition-colors`}
            >
              {item.label}
            </button>
          ))}
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          🚪 Logout
        </button>
      </div>
    </div>
  )
}

export default Navigation 