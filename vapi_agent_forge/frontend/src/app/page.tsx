'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface SystemStatus {
  services: Record<string, any>;
  deployment: any;
  environment: {
    public_server_url: string;
    vapi_api_key_set: boolean;
    ngrok_active: boolean;
  };
  configuration: {
    tools_count: number;
    assistant_configured: boolean;
  };
}

export default function LandingPage() {
  const router = useRouter()
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showClearData, setShowClearData] = useState(false)

  useEffect(() => {
    // Check if there's cached user data
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      setShowClearData(true)
    }

    // Fetch system status to show platform health
    fetchSystemStatus()
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/status')
      const data = await response.json()
      setSystemStatus(data)
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGetStarted = () => {
    router.push('/login')
  }

  const handleClearData = () => {
    localStorage.clear()
    setShowClearData(false)
    window.location.reload()
  }

  const handleGoToDashboard = () => {
    router.push('/agents')
  }

  const handleLearnMore = () => {
    // Scroll to features section
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white/30 mx-auto"></div>
          <p className="mt-4 text-white/70">Loading platform...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              🎙️
            </div>
            <span className="text-xl font-bold">Vapi Bridge</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${systemStatus?.environment.ngrok_active ? 'bg-green-400' : 'bg-yellow-400'}`}></div>
              <span className="text-white/70">Platform Online</span>
            </div>
            {showClearData && (
              <button
                onClick={handleClearData}
                className="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 rounded text-sm transition-colors"
              >
                Clear Data
              </button>
            )}
            {showClearData ? (
              <button
                onClick={handleGoToDashboard}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
              >
                Go to Dashboard
              </button>
            ) : (
              <button
                onClick={handleGetStarted}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Alert for cached data */}
      {showClearData && (
        <div className="container mx-auto px-6">
          <div className="bg-yellow-600/20 border border-yellow-500/30 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <h3 className="font-semibold">Cached User Data Found</h3>
                  <p className="text-sm text-white/70">You have existing user data. You can continue to your dashboard or clear data for a fresh start.</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleGoToDashboard}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors text-sm"
                >
                  Continue to Dashboard
                </button>
                <button
                  onClick={handleClearData}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors text-sm"
                >
                  Clear & Start Fresh
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <div className="container mx-auto px-6 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
            Voice AI for Your Business
          </h1>
          <p className="text-xl text-white/80 mb-8 leading-relaxed">
            Create unlimited voice agents that connect to your existing APIs. 
            No code deployment required - just configure your services and start talking.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <button
              onClick={handleGetStarted}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg text-lg font-semibold transition-all transform hover:scale-105"
            >
              🚀 Get Started Free
            </button>
            <button
              onClick={handleLearnMore}
              className="px-8 py-4 bg-white/10 hover:bg-white/20 rounded-lg text-lg font-semibold transition-colors border border-white/20"
            >
              📖 Learn More
            </button>
          </div>

          {/* Platform Status */}
          {systemStatus && (
            <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-white/10 max-w-2xl mx-auto">
              <div className="flex items-center justify-center gap-8 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>Backend Online</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${systemStatus.environment.ngrok_active ? 'bg-green-400' : 'bg-yellow-400'}`}></div>
                  <span>{systemStatus.environment.ngrok_active ? 'Public Access' : 'Local Mode'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span>{Object.keys(systemStatus.services).length} Services</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Access Section */}
      <div className="container mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Quick Access</h2>
          <p className="text-white/70">Jump directly to any part of the platform</p>
        </div>
        
        <div className="grid md:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <button
            onClick={() => router.push('/login')}
            className="bg-white/5 hover:bg-white/10 backdrop-blur rounded-lg p-6 border border-white/10 transition-colors text-center"
          >
            <div className="text-3xl mb-3">🏢</div>
            <h3 className="font-semibold mb-2">Company Login</h3>
            <p className="text-sm text-white/70">Sign up or sign in</p>
          </button>
          
          <button
            onClick={() => router.push('/agents')}
            className="bg-white/5 hover:bg-white/10 backdrop-blur rounded-lg p-6 border border-white/10 transition-colors text-center"
          >
            <div className="text-3xl mb-3">🤖</div>
            <h3 className="font-semibold mb-2">Voice Agents</h3>
            <p className="text-sm text-white/70">Manage your agents</p>
          </button>
          
          <button
            onClick={() => {
              // If user exists, go to agents page with services tab
              const storedUser = localStorage.getItem('user')
              if (storedUser) {
                router.push('/agents?tab=services')
              } else {
                router.push('/login')
              }
            }}
            className="bg-white/5 hover:bg-white/10 backdrop-blur rounded-lg p-6 border border-white/10 transition-colors text-center"
          >
            <div className="text-3xl mb-3">🛠️</div>
            <h3 className="font-semibold mb-2">Service Registry</h3>
            <p className="text-sm text-white/70">Configure your APIs</p>
          </button>
          
          <button
            onClick={() => window.open('http://localhost:8000/docs', '_blank')}
            className="bg-white/5 hover:bg-white/10 backdrop-blur rounded-lg p-6 border border-white/10 transition-colors text-center"
          >
            <div className="text-3xl mb-3">📚</div>
            <h3 className="font-semibold mb-2">API Docs</h3>
            <p className="text-sm text-white/70">Backend API reference</p>
          </button>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Why Choose Vapi Bridge?</h2>
          <p className="text-xl text-white/70">Everything you need to add voice AI to your business</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* No Code Required */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center text-2xl mb-4">
              🚫
            </div>
            <h3 className="text-xl font-semibold mb-3">No Code Required</h3>
            <p className="text-white/70">
              Configure your APIs through our web interface. No server setup, no code deployment, no technical complexity.
            </p>
          </div>

          {/* Instant Integration */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center text-2xl mb-4">
              ⚡
            </div>
            <h3 className="text-xl font-semibold mb-3">Instant Integration</h3>
            <p className="text-white/70">
              Connect your existing REST APIs in minutes. Real-time health monitoring and automatic URL resolution.
            </p>
          </div>

          {/* Unlimited Agents */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center text-2xl mb-4">
              🤖
            </div>
            <h3 className="text-xl font-semibold mb-3">Unlimited Voice Agents</h3>
            <p className="text-white/70">
              Create as many voice assistants as you need. Each one can use different services and configurations.
            </p>
          </div>

          {/* Enterprise Ready */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center text-2xl mb-4">
              🏢
            </div>
            <h3 className="text-xl font-semibold mb-3">Enterprise Ready</h3>
            <p className="text-white/70">
              Multi-tenant architecture, interaction logging, usage analytics, and white-label deployment options.
            </p>
          </div>

          {/* Template Library */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="w-12 h-12 bg-pink-500/20 rounded-lg flex items-center justify-center text-2xl mb-4">
              📋
            </div>
            <h3 className="text-xl font-semibold mb-3">Template Library</h3>
            <p className="text-white/70">
              Quick-start templates for research assistants, workflow automation, customer support, and more.
            </p>
          </div>

          {/* Vapi Powered */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center text-2xl mb-4">
              🎙️
            </div>
            <h3 className="text-xl font-semibold mb-3">Vapi Powered</h3>
            <p className="text-white/70">
              Built on Vapi's proven voice infrastructure. Reliable, scalable, and optimized for business use.
            </p>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">How It Works</h2>
          <p className="text-xl text-white/70">Get started in minutes, not hours</p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                1️⃣
              </div>
              <h3 className="text-xl font-semibold mb-3">Sign Up & Configure</h3>
              <p className="text-white/70">
                Create your account and add your API endpoints through our simple web interface.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                2️⃣
              </div>
              <h3 className="text-xl font-semibold mb-3">Create Voice Agents</h3>
              <p className="text-white/70">
                Use our templates or YAML editor to create voice assistants that use your services.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                3️⃣
              </div>
              <h3 className="text-xl font-semibold mb-3">Start Talking</h3>
              <p className="text-white/70">
                Your voice agents are ready to handle calls and interact with your business systems.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Preview */}
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
          <p className="text-xl text-white/70">Choose the plan that fits your business</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {/* Basic Plan */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10">
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2">Basic</h3>
              <div className="text-4xl font-bold mb-4">$99<span className="text-lg text-white/70">/month</span></div>
              <ul className="text-left space-y-3 mb-8">
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>5 configured services</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>10 voice agents</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Basic analytics</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Email support</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Pro Plan */}
          <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 backdrop-blur rounded-lg p-8 border border-blue-500/30 relative">
            <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                Most Popular
              </span>
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2">Pro</h3>
              <div className="text-4xl font-bold mb-4">$299<span className="text-lg text-white/70">/month</span></div>
              <ul className="text-left space-y-3 mb-8">
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>20 configured services</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>50 voice agents</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Advanced analytics</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Priority support</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Enterprise Plan */}
          <div className="bg-white/5 backdrop-blur rounded-lg p-8 border border-white/10">
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2">Enterprise</h3>
              <div className="text-4xl font-bold mb-4">$999<span className="text-lg text-white/70">/month</span></div>
              <ul className="text-left space-y-3 mb-8">
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Unlimited services</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Unlimited voice agents</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>White-label deployment</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Dedicated support</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur rounded-lg p-12 border border-blue-500/30 text-center">
          <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl text-white/80 mb-8">
            Join companies already using Vapi Bridge to power their voice AI
          </p>
          <button
            onClick={handleGetStarted}
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg text-lg font-semibold transition-all transform hover:scale-105"
          >
            🚀 Start Your Free Trial
          </button>
          <p className="text-sm text-white/60 mt-4">
            No credit card required • Setup in minutes • Cancel anytime
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-8 border-t border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center text-sm">
              🎙️
            </div>
            <span className="font-medium">Vapi Bridge</span>
          </div>
          <div className="text-sm text-white/60">
            © 2024 Vapi Bridge. Powered by voice AI.
          </div>
        </div>
      </footer>
    </div>
  )
}
