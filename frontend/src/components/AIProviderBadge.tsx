'use client'

import { useState, useEffect } from 'react'
import { Cpu, Sparkles, Zap, Cloud, Server, HardDrive } from 'lucide-react'

interface AIProvider {
  provider: string
  model: string
  provider_name: string
  model_name: string
  description: string
  capabilities: string[]
  badge_color: string
}

interface AIProviderBadgeProps {
  className?: string
  showDetails?: boolean
}

export default function AIProviderBadge({ className = '', showDetails = false }: AIProviderBadgeProps) {
  const [provider, setProvider] = useState<AIProvider | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProviderInfo = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
        const response = await fetch(`${apiUrl}/ai/provider`)
        const data = await response.json()
        setProvider(data)
      } catch (error) {
        console.error('Error fetching AI provider info:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchProviderInfo()
  }, [])

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 px-3 py-1 bg-gray-100 rounded-full ${className}`}>
        <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
        <span className="text-xs text-gray-600">Loading AI...</span>
      </div>
    )
  }

  if (!provider) {
    return null
  }

  const getIcon = () => {
    switch (provider.provider) {
      case 'openai':
        return <Sparkles className="h-3 w-3" />
      case 'zai':
        return <Cpu className="h-3 w-3" />
      case 'openrouter':
        return <Zap className="h-3 w-3" />
      case 'ollama':
      case 'lmstudio':
        return <Server className="h-3 w-3" />
      default:
        return <Cloud className="h-3 w-3" />
    }
  }

  const getBadgeColor = () => {
    switch (provider.badge_color) {
      case 'green':
        return 'bg-green-100 text-green-700 border-green-200'
      case 'blue':
        return 'bg-blue-100 text-blue-700 border-blue-200'
      case 'purple':
        return 'bg-purple-100 text-purple-700 border-purple-200'
      case 'orange':
        return 'bg-orange-100 text-orange-700 border-orange-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getProgressiveColor = () => {
    switch (provider.badge_color) {
      case 'green':
        return 'from-green-500 to-emerald-600'
      case 'blue':
        return 'from-blue-500 to-indigo-600'
      case 'purple':
        return 'from-purple-500 to-pink-600'
      case 'orange':
        return 'from-orange-500 to-red-600'
      default:
        return 'from-gray-500 to-gray-600'
    }
  }

  if (showDetails) {
    return (
      <div className={`relative group ${className}`}>
        <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${getBadgeColor()} bg-gradient-to-r ${getProgressiveColor()} text-white shadow-lg`}>
          {getIcon()}
          <div className="flex flex-col">
            <span className="text-xs font-semibold">{provider.provider_name}</span>
            <span className="text-xs opacity-90">{provider.model_name}</span>
          </div>
        </div>

        {/* Tooltip with details */}
        <div className="absolute bottom-full right-0 mb-2 w-64 p-3 bg-white rounded-lg shadow-xl border border-gray-200 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
          <div className="space-y-2">
            <div>
              <h4 className="font-semibold text-sm text-gray-900">{provider.provider_name}</h4>
              <p className="text-xs text-gray-600">{provider.description}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-700 mb-1">Model:</p>
              <p className="text-xs text-gray-600">{provider.model_name}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-700 mb-1">Capabilities:</p>
              <div className="flex flex-wrap gap-1">
                {provider.capabilities.map((capability, index) => (
                  <span key={index} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                    {capability}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex items-center space-x-1 px-2 py-1 rounded-full border ${getBadgeColor()} ${className}`}>
      {getIcon()}
      <span className="text-xs font-medium">{provider.provider_name}</span>
    </div>
  )
}