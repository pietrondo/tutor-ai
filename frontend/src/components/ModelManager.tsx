'use client'

import { useState, useEffect } from 'react'
import { Brain, Server, CheckCircle, AlertCircle, RefreshCw, DollarSign, Zap, Clock, Monitor, Cpu, Wifi, WifiOff } from 'lucide-react'

interface Model {
  name: string
  displayName: string
  context_window: number
  max_tokens: number
  description: string
  use_cases: string[]
  cost_per_1k_tokens?: {
    input: number
    output: number
  }
  recommended_vram?: string
  provider?: string
}

interface ModelData {
  models: Record<string, Model>
  current_model: string
  budget_mode: boolean
  model_type: string
  local_connection?: boolean
  available_models?: string[]
  error?: string
}

// Add displayName mapping for better UI
const MODEL_DISPLAY_NAMES: Record<string, string> = {
  'gpt-4o': 'GPT-4 Omni',
  'gpt-4o-mini': 'GPT-4o Mini',
  'gpt-4-turbo': 'GPT-4 Turbo',
  'gpt-4': 'GPT-4',
  'gpt-3.5-turbo': 'GPT-3.5 Turbo'
}

export default function ModelManager() {
  const [modelData, setModelData] = useState<ModelData | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState('')
  const [testingConnection, setTestingConnection] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<any>(null)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/models')
      if (response.ok) {
        const data = await response.json()

        // Process the models data to add displayName
        const processedModels: Record<string, Model> = {}
        Object.entries(data.models).forEach(([key, model]) => {
          const modelData = model as any // Cast to any to handle dynamic API response
          processedModels[key] = {
            name: modelData.name,
            displayName: MODEL_DISPLAY_NAMES[key] || modelData.name || key,
            context_window: modelData.context_window,
            max_tokens: modelData.max_tokens,
            description: modelData.description,
            use_cases: modelData.use_cases,
            cost_per_1k_tokens: modelData.cost_per_1k_tokens,
            recommended_vram: modelData.recommended_vram,
            provider: modelData.provider
          }
        })

        setModelData({
          ...data,
          models: processedModels
        })
        setSelectedModel(data.current_model)
      }
    } catch (error) {
      console.error('Errore nel caricamento dei modelli:', error)
    } finally {
      setLoading(false)
    }
  }

  const setModel = async (modelName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/models/${modelName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setSelectedModel(modelName)
        fetchModels() // Refresh data
      }
    } catch (error) {
      console.error('Errore nell\'impostazione del modello:', error)
    }
  }

  const toggleBudgetMode = async () => {
    if (!modelData) return

    try {
      const response = await fetch('http://localhost:8000/models/budget-mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          enabled: !modelData.budget_mode
        })
      })

      if (response.ok) {
        fetchModels() // Refresh data
      }
    } catch (error) {
      console.error('Errore nell\'impostazione della modalità budget:', error)
    }
  }

  const testLocalConnection = async () => {
    setTestingConnection(true)
    try {
      const response = await fetch('http://localhost:8000/models/local/test')
      if (response.ok) {
        const data = await response.json()
        setConnectionStatus(data)
      }
    } catch (error) {
      console.error('Errore nel test della connessione:', error)
    } finally {
      setTestingConnection(false)
    }
  }

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`
  }

  const getUseCaseIcon = (useCase: string) => {
    switch (useCase) {
      case 'chat': return <Zap className="h-4 w-4" />
      case 'quiz': return <CheckCircle className="h-4 w-4" />
      case 'study_plans': return <Clock className="h-4 w-4" />
      case 'complex_reasoning': return <Brain className="h-4 w-4" />
      case 'coding': return <Cpu className="h-4 w-4" />
      default: return <Monitor className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2">Caricamento modelli...</span>
      </div>
    )
  }

  if (!modelData) {
    return (
      <div className="text-center p-8 text-red-600">
        <AlertCircle className="h-8 w-8 mx-auto mb-2" />
        Impossibile caricare i modelli
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Gestione Modelli AI
          </h3>
          <p className="text-gray-600 text-sm mt-1">
            Provider: <span className="font-semibold capitalize">{modelData.model_type}</span>
          </p>
        </div>

        {/* Budget Mode Toggle */}
        <div className="flex items-center space-x-3">
          <DollarSign className="h-5 w-5 text-green-600" />
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={modelData.budget_mode}
              onChange={toggleBudgetMode}
              className="sr-only"
            />
            <div className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              modelData.budget_mode ? 'bg-green-500' : 'bg-gray-300'
            }`}>
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                modelData.budget_mode ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </div>
            <span className="ml-2 text-sm font-medium">
              Modalità Budget {modelData.budget_mode ? 'ON' : 'OFF'}
            </span>
          </label>
        </div>
      </div>

      {/* Local Connection Status */}
      {modelData.model_type !== 'openai' && (
        <div className="glass-card rounded-xl p-4 border border-gray-200/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${
                modelData.local_connection ? 'bg-green-100' : 'bg-red-100'
              }`}>
                {modelData.local_connection ?
                  <Wifi className="h-4 w-4 text-green-600" /> :
                  <WifiOff className="h-4 w-4 text-red-600" />
                }
              </div>
              <div>
                <p className="text-sm font-medium">Connessione Locale</p>
                <p className="text-xs text-gray-500">
                  {modelData.model_type === 'ollama' ? 'Ollama' : 'LM Studio'}
                </p>
              </div>
            </div>

            <button
              onClick={testLocalConnection}
              disabled={testingConnection}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-1"
            >
              {testingConnection ? (
                <RefreshCw className="h-3 w-3 animate-spin" />
              ) : (
                <Server className="h-3 w-3" />
              )}
              <span>Test</span>
            </button>
          </div>

          {connectionStatus && (
            <div className="mt-3 p-2 bg-gray-50 rounded-lg text-xs">
              <p>Stato: {connectionStatus.connected ? 'Connesso' : 'Non connesso'}</p>
              {connectionStatus.available_models?.length > 0 && (
                <p>Modelli: {connectionStatus.available_models.join(', ')}</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Model Selection */}
      <div className="space-y-4">
        <h4 className="font-semibold text-gray-800 flex items-center">
          <Brain className="h-4 w-4 mr-2" />
          Selezione Modello
        </h4>

        <select
          value={selectedModel}
          onChange={(e) => setModel(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {Object.entries(modelData.models).map(([key, model]) => (
            <option key={key} value={key}>
              {model.displayName} - {model.description.substring(0, 50)}...
            </option>
          ))}
        </select>
      </div>

      {/* Available Models Grid */}
      <div className="space-y-4">
        <h4 className="font-semibold text-gray-800">Modelli Disponibili</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(modelData.models).map(([key, model]) => (
            <div
              key={key}
              className={`glass-card rounded-xl p-4 border transition-all cursor-pointer hover:shadow-lg ${
                selectedModel === key
                  ? 'border-blue-500 bg-blue-50/50'
                  : 'border-gray-200/50 hover:border-gray-300/50'
              }`}
              onClick={() => setModel(key)}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h5 className="font-semibold text-gray-900">{model.displayName}</h5>
                  <p className="text-xs text-gray-500 mt-1">{key}</p>
                </div>

                {selectedModel === key && (
                  <CheckCircle className="h-5 w-5 text-blue-500" />
                )}
              </div>

              <p className="text-sm text-gray-600 mb-3">{model.description}</p>

              {/* Use Cases */}
              <div className="flex flex-wrap gap-1 mb-3">
                {model.use_cases.slice(0, 3).map((useCase) => (
                  <span
                    key={useCase}
                    className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                  >
                    {getUseCaseIcon(useCase)}
                    <span className="ml-1">{useCase}</span>
                  </span>
                ))}
              </div>

              {/* Model Info */}
              <div className="space-y-1 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Context:</span>
                  <span className="font-medium">{model.context_window.toLocaleString()} tokens</span>
                </div>

                {model.cost_per_1k_tokens && (
                  <>
                    <div className="flex justify-between">
                      <span>Costo Input:</span>
                      <span className="font-medium">{formatCost(model.cost_per_1k_tokens.input)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Costo Output:</span>
                      <span className="font-medium">{formatCost(model.cost_per_1k_tokens.output)}</span>
                    </div>
                  </>
                )}

                {model.recommended_vram && (
                  <div className="flex justify-between">
                    <span>VRAM Consigliata:</span>
                    <span className="font-medium">{model.recommended_vram}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {modelData.error && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          <AlertCircle className="h-4 w-4 inline mr-2" />
          {modelData.error}
        </div>
      )}
    </div>
  )
}