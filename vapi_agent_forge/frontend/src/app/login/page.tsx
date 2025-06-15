'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: number
  username: string
  email?: string
  created_at: string
  vapi_configured: boolean
}

const LoginPage: React.FC = () => {
  const router = useRouter()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [vapiApiKey, setVapiApiKey] = useState('')
  const [vapiPublicKey, setVapiPublicKey] = useState('')
  const [existingUsers, setExistingUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showVapiKeys, setShowVapiKeys] = useState(false)

  useEffect(() => {
    loadExistingUsers()
  }, [])

  const loadExistingUsers = async () => {
    try {
      const response = await fetch('http://localhost:8000/auth/users')
      const data = await response.json()
      if (data.status === 'success') {
        setExistingUsers(data.users)
      }
    } catch (error) {
      console.error('Failed to load users:', error)
    }
  }

  const handleSignup = async () => {
    if (!username.trim()) {
      setError('Please enter a company username')
      return
    }
    if (!vapiApiKey.trim()) {
      setError('Please enter your VAPI API key')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username: username.trim(),
          email: email.trim() || null,
          vapi_api_key: vapiApiKey.trim(),
          vapi_public_key: vapiPublicKey.trim() || null
        }),
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify({
          id: data.user_id,
          username: data.username,
          email: data.email,
          vapi_configured: data.vapi_configured
        }))
        
        // Redirect to agents page
        router.push('/agents')
      } else {
        setError(data.detail || 'Signup failed')
      }
    } catch (error) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogin = async (selectedUsername?: string, updateVapi = false) => {
    const loginUsername = selectedUsername || username
    if (!loginUsername.trim()) {
      setError('Please enter a username')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const loginData: any = { username: loginUsername }
      
      // Include VAPI keys if updating or if provided
      if (updateVapi && vapiApiKey.trim()) {
        loginData.vapi_api_key = vapiApiKey.trim()
        loginData.vapi_public_key = vapiPublicKey.trim() || null
      }

      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify({
          id: data.user_id,
          username: data.username,
          email: data.email,
          vapi_configured: data.vapi_configured
        }))
        
        // Redirect to agents page
        router.push('/agents')
      } else {
        setError('Login failed')
      }
    } catch (error) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center px-4">
      <div className="max-w-lg w-full bg-white/10 backdrop-blur-md rounded-lg p-8 border border-white/20">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center text-3xl mx-auto mb-4">
            🎙️
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Vapi Bridge</h1>
          <p className="text-gray-300">Voice AI for your business</p>
        </div>

        {/* Mode Toggle */}
        <div className="flex mb-6 bg-white/5 rounded-lg p-1">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              mode === 'login' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setMode('signup')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              mode === 'signup' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Sign Up
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        {mode === 'signup' ? (
          /* Signup Form */
          <div className="space-y-4">
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Company Username *
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g., researchers, acme_corp"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Email (Optional)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@company.com"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                VAPI API Key *
              </label>
              <input
                type="password"
                value={vapiApiKey}
                onChange={(e) => setVapiApiKey(e.target.value)}
                placeholder="Your VAPI API key from dashboard"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-400 mt-1">
                Get your API key from <a href="https://dashboard.vapi.ai" target="_blank" className="text-blue-400 hover:text-blue-300">Vapi Dashboard</a>
              </p>
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                VAPI Public Key (Optional)
              </label>
              <input
                type="text"
                value={vapiPublicKey}
                onChange={(e) => setVapiPublicKey(e.target.value)}
                placeholder="Your VAPI public key (for web calls)"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={handleSignup}
              disabled={isLoading}
              className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg font-medium transition-colors"
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </div>
        ) : (
          /* Login Form */
          <div>
            <div className="mb-4">
              <label className="block text-white text-sm font-medium mb-2">
                Company Username
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g., researchers, acme_corp"
                  className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                />
                <button
                  onClick={() => handleLogin()}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg font-medium transition-colors"
                >
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </button>
              </div>
            </div>

            {/* VAPI Key Update Section */}
            <div className="mb-4">
              <button
                onClick={() => setShowVapiKeys(!showVapiKeys)}
                className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
              >
                {showVapiKeys ? '− Hide' : '+ Update'} VAPI API Keys
              </button>
              
              {showVapiKeys && (
                <div className="mt-3 space-y-3 p-3 bg-white/5 rounded-lg border border-white/10">
                  <div>
                    <label className="block text-white text-xs font-medium mb-1">
                      VAPI API Key
                    </label>
                    <input
                      type="password"
                      value={vapiApiKey}
                      onChange={(e) => setVapiApiKey(e.target.value)}
                      placeholder="Update your VAPI API key"
                      className="w-full px-2 py-1 text-sm bg-white/10 border border-white/20 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-white text-xs font-medium mb-1">
                      VAPI Public Key (Optional)
                    </label>
                    <input
                      type="text"
                      value={vapiPublicKey}
                      onChange={(e) => setVapiPublicKey(e.target.value)}
                      placeholder="Update your VAPI public key"
                      className="w-full px-2 py-1 text-sm bg-white/10 border border-white/20 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    onClick={() => handleLogin(username, true)}
                    disabled={isLoading}
                    className="w-full py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 text-white rounded text-sm font-medium transition-colors"
                  >
                    Sign In & Update Keys
                  </button>
                </div>
              )}
            </div>

            {/* Existing Users */}
            {existingUsers.length > 0 && (
              <div>
                <h3 className="text-white text-sm font-medium mb-3">Or select existing company:</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {existingUsers.map((user) => (
                    <button
                      key={user.id}
                      onClick={() => handleLogin(user.username)}
                      disabled={isLoading}
                      className="w-full text-left px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{user.username}</div>
                          <div className="text-xs text-gray-400">
                            Created: {new Date(user.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {user.vapi_configured ? (
                            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                              VAPI ✓
                            </span>
                          ) : (
                            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                              No VAPI
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="mt-8 text-center">
          <button
            onClick={() => router.push('/')}
            className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
          >
            ← Back to Home
          </button>
        </div>

        <div className="mt-4 text-center text-xs text-gray-400">
          Each company uses their own VAPI API key for voice agents
        </div>
      </div>
    </div>
  )
}

export default LoginPage 