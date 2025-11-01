'use client'

import { useState, useEffect } from 'react'
import {
  Settings,
  CheckCircle,
  XCircle,
  AlertCircle,
  Key,
  Globe,
  Brain,
  Zap,
  RefreshCw,
  Eye,
  EyeOff,
  Server,
  Cloud,
  DollarSign,
  BarChart3
} from 'lucide-react'
import { llmManager, LLMProvider } from '@/lib/llm-manager'

interface LLMProviderConfigProps {
  onConfigurationChange?: (providers: LLMProvider[]) => void
}

export function LLMProviderConfig({ onConfigurationChange }: LLMProviderConfigProps) {
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [checkingProvider, setCheckingProvider] = useState<string | null>(null)
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = () => {
    const allProviders = llmManager.getAllProviders()
    setProviders(allProviders)

    // Initialize showApiKeys state
    const initialShowKeys: Record<string, boolean> = {}
    allProviders.forEach(provider => {
      initialShowKeys[provider.id] = false
    })
    setShowApiKeys(initialShowKeys)
  }

  const checkProviderAvailability = async (providerId: string) => {
    setCheckingProvider(providerId)
    try {
      const isAvailable = await llmManager.checkProviderAvailability(providerId)
      setTestResults(prev => ({
        ...prev,
        [providerId]: {
          success: isAvailable,
          message: isAvailable ? 'Provider disponibile e funzionante' : 'Provider non raggiungibile'
        }
      }))
      loadProviders() // Reload to update availability status
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [providerId]: {
          success: false,
          message: error instanceof Error ? error.message : 'Errore durante il test'
        }
      }))
    } finally {
      setCheckingProvider(null)
    }
  }

  const checkAllProviders = async () => {
    await llmManager.checkAllProvidersAvailability()
    loadProviders()
  }

  const updateProviderConfig = (providerId: string, updates: Partial<LLMProvider>) => {
    llmManager.configureProvider(providerId, updates)
    loadProviders()
    if (onConfigurationChange) {
      onConfigurationChange(llmManager.getAllProviders())
    }
  }

  const toggleApiKeyVisibility = (providerId: string) => {
    setShowApiKeys(prev => ({
      ...prev,
      [providerId]: !prev[providerId]
    }))
  }

  const getProviderIcon = (type: LLMProvider['type']) => {
    switch (type) {
      case 'openai':
        return <Brain className="h-5 w-5" />
      case 'openrouter':
        return <Globe className="h-5 w-5" />
      case 'local':
        return <Server className="h-5 w-5" />
      case 'anthropic':
        return <Zap className="h-5 w-5" />
      default:
        return <Cloud className="h-5 w-5" />
    }
  }

  const renderProviderCard = (provider: LLMProvider) => (
    <div key={provider.id} className="glass rounded-xl p-6 border border-gray-200/50">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${
            provider.isAvailable ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'
          }`}>
            {getProviderIcon(provider.type)}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{provider.name}</h3>
            <p className="text-sm text-gray-600">{provider.model}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {provider.isAvailable ? (
            <CheckCircle className="h-5 w-5 text-green-600" />
          ) : (
            <XCircle className="h-5 w-5 text-gray-400" />
          )}
          <button
            onClick={() => checkProviderAvailability(provider.id)}
            disabled={checkingProvider === provider.id}
            className="btn btn-secondary btn-sm"
          >
            {checkingProvider === provider.id ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              'Test'
            )}
          </button>
        </div>
      </div>

      {/* Test Result */}
      {testResults[provider.id] && (
        <div className={`mb-4 p-3 rounded-lg border ${
          testResults[provider.id].success
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            {testResults[provider.id].success ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <span className={`text-sm ${
              testResults[provider.id].success ? 'text-green-800' : 'text-red-800'
            }`}>
              {testResults[provider.id].message}
            </span>
          </div>
        </div>
      )}

      {/* Configuration */}
      <div className="space-y-4">
        {/* API Key */}
        {(provider.type === 'openai' || provider.type === 'openrouter' || provider.type === 'anthropic') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key
            </label>
            <div className="flex space-x-2">
              <div className="flex-1 relative">
                <input
                  type={showApiKeys[provider.id] ? 'text' : 'password'}
                  value={provider.apiKey || ''}
                  onChange={(e) => updateProviderConfig(provider.id, { apiKey: e.target.value })}
                  placeholder="Inserisci la tua API key"
                  className="form-input pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleApiKeyVisibility(provider.id)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showApiKeys[provider.id] ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Base URL (for custom providers) */}
        {provider.type === 'local' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Base URL
            </label>
            <input
              type="text"
              value={provider.baseUrl || ''}
              onChange={(e) => updateProviderConfig(provider.id, { baseUrl: e.target.value })}
              placeholder="http://localhost:1234/v1"
              className="form-input"
            />
          </div>
        )}

        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Modello
          </label>
          <select
            value={provider.model}
            onChange={(e) => updateProviderConfig(provider.id, { model: e.target.value })}
            className="form-input"
          >
            {provider.type === 'openai' && (
              <>
                <option value="gpt-4-turbo-preview">GPT-4 Turbo Preview</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </>
            )}
            {provider.type === 'openrouter' && (
              <>
                <option value="meta-llama/llama-3.2-3b-instruct:free">Llama 3.2 3B (Free)</option>
                <option value="meta-llama/llama-3.1-8b-instruct:free">Llama 3.1 8B (Free)</option>
                <option value="microsoft/wizardlm-2-8x22b">WizardLM 2 8x22B</option>
                <option value="openai/gpt-4-turbo-preview">GPT-4 Turbo Preview</option>
              </>
            )}
            {provider.type === 'anthropic' && (
              <>
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                <option value="claude-3-opus-20240229">Claude 3 Opus</option>
              </>
            )}
            {provider.type === 'local' && (
              <option value="local-model">Local Model</option>
            )}
          </select>
        </div>

        {/* Parameters */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature (0-2)
            </label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={provider.temperature}
              onChange={(e) => updateProviderConfig(provider.id, { temperature: parseFloat(e.target.value) })}
              className="form-input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              min="1"
              max="32000"
              value={provider.maxTokens}
              onChange={(e) => updateProviderConfig(provider.id, { maxTokens: parseInt(e.target.value) })}
              className="form-input"
            />
          </div>
        </div>

        {/* Capabilities */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Capacità
          </label>
          <div className="flex flex-wrap gap-2">
            {provider.capabilities.streaming && (
              <span className="badge badge-primary text-xs">Streaming</span>
            )}
            {provider.capabilities.functionCalling && (
              <span className="badge badge-primary text-xs">Function Calling</span>
            )}
            {provider.capabilities.imageAnalysis && (
              <span className="badge badge-primary text-xs">Image Analysis</span>
            )}
            {provider.capabilities.codeExecution && (
              <span className="badge badge-primary text-xs">Code Execution</span>
            )}
          </div>
        </div>

        {/* Cost Information */}
        {provider.costPerToken && (
          <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center space-x-2 text-sm text-yellow-800">
              <DollarSign className="h-4 w-4" />
              <span>Costo: ${provider.costPerToken.toFixed(6)} per token</span>
            </div>
          </div>
        )}

        {/* Context Window */}
        <div className="text-sm text-gray-600">
          <span className="font-medium">Context Window:</span> {provider.contextWindow.toLocaleString()} tokens
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <Settings className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Configurazione Provider LLM
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Gestisci OpenAI, OpenRouter, LM Studio locale e altri provider
              </p>
            </div>
          </div>
          <button
            onClick={checkAllProviders}
            className="btn btn-secondary"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Controlla Tutti
          </button>
        </div>

        {/* Provider Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-xl font-bold text-green-600">
              {providers.filter(p => p.isAvailable).length}
            </div>
            <p className="text-xs text-gray-600">Provider Disponibili</p>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-xl font-bold text-blue-600">
              {providers.length}
            </div>
            <p className="text-xs text-gray-600">Totali Configurati</p>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-xl font-bold text-purple-600">
              {providers.filter(p => p.capabilities.streaming).length}
            </div>
            <p className="text-xs text-gray-600">Supportano Streaming</p>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-xl font-bold text-orange-600">
              {Math.max(...providers.map(p => p.contextWindow)).toLocaleString()}
            </div>
            <p className="text-xs text-gray-600">Max Context Window</p>
          </div>
        </div>
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {providers.map(renderProviderCard)}
      </div>

      {/* Quick Setup Guide */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Guida Rapida Configurazione</h4>
        <div className="space-y-4">
          <div className="flex items-start space-x-3 p-4 bg-blue-50 rounded-lg">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Globe className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <h5 className="font-medium text-blue-900">OpenRouter (Consigliato per iniziare)</h5>
              <p className="text-sm text-blue-700 mt-1">
                Ottieni una API key gratuita da OpenRouter per accedere a molti modelli senza costi.
                Supporta modelli gratuiti come Llama 3.2 e Claude 3 Haiku.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-4 bg-green-50 rounded-lg">
            <div className="p-2 bg-green-100 rounded-lg">
              <Server className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <h5 className="font-medium text-green-900">LM Studio Locale</h5>
              <p className="text-sm text-green-700 mt-1">
                Scarica LM Studio e avvia modelli localmente per privacy completa e nessun costo.
                Assicurati che il server sia in esecuzione su http://localhost:1234
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-4 bg-purple-50 rounded-lg">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="h-4 w-4 text-purple-600" />
            </div>
            <div>
              <h5 className="font-medium text-purple-900">OpenAI</h5>
              <p className="text-sm text-purple-700 mt-1">
                Per le migliori performance, configura la tua API key di OpenAI.
                Supporta GPT-4 Turbo con funzionalità avanzate.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Fallback Chain Configuration */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-4">
          <BarChart3 className="h-5 w-5 text-gray-600" />
          <h4 className="font-semibold text-gray-900">Catena di Fallback</h4>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Configura l'ordine in cui il sistema tenterà i provider se quello primario non è disponibile.
        </p>
        <div className="text-sm text-gray-500">
          Catena attuale: Local → OpenRouter → OpenAI → Anthropic
        </div>
      </div>
    </div>
  )
}