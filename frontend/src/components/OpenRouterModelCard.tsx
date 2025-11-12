'use client'

import { CheckCircle, RefreshCw, Eye, Zap, Star, Crown } from 'lucide-react'
import type { OpenRouterModel } from '@/hooks/useOpenRouterModels'

interface OpenRouterModelCardProps {
  model: OpenRouterModel
  selected: boolean
  onSelect: () => void
  validation?: {
    valid: boolean
    message: string
    loading: boolean
  }
}

export default function OpenRouterModelCard({ model, selected, onSelect, validation }: OpenRouterModelCardProps) {
  const totalCost = (model.cost_per_input_1k || 0) + (model.cost_per_output_1k || 0)

  return (
    <div
      onClick={onSelect}
      className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 ${
        selected
          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 dark:border-purple-400'
          : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
      } ${validation?.loading ? 'opacity-75' : ''}`}
    >
      {/* Selected indicator */}
      {selected && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full border-2 border-white dark:border-gray-900"></div>
      )}

      {/* Validation status indicator */}
      <div className="absolute top-2 right-2">
        {validation?.loading && (
          <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
        )}
        {validation?.valid && (
          <CheckCircle className="h-4 w-4 text-green-500" />
        )}
        {validation?.valid === false && (
          <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center" title="Modello non funzionante">
            <span className="text-white text-xs">×</span>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {/* Model Name and Provider */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h5 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center space-x-2">
              <span>{model.display_name || model.name}</span>
              {model.category === 'RECOMMENDED' && <Star className="h-4 w-4 text-yellow-500" />}
              {model.is_premium && <Crown className="h-4 w-4 text-purple-500" />}
            </h5>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {model.provider_short || model.provider}
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
          {model.description}
        </p>

        {/* Capabilities */}
        <div className="flex flex-wrap gap-1">
          {model.supports_vision && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
              <Eye className="h-3 w-3 mr-1" />
              Visione
            </span>
          )}
          {model.supports_streaming && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              <Zap className="h-3 w-3 mr-1" />
              Streaming
            </span>
          )}
          {model.category && (
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
              ${model.category === 'PREMIUM' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' : ''}
              ${model.category === 'ECONOMY' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : ''}
              ${model.category === 'BALANCED' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' : ''}
              ${model.category === 'VISION' ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200' : ''}
              ${model.category === 'SPECIALIZED' ? 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200' : ''}
            `}>
              {model.category}
            </span>
          )}
        </div>

        {/* Specs */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Context: {model.context_window.toLocaleString()}</span>
          <span className="font-medium">
            ${totalCost.toFixed(4)}/1K tokens
          </span>
        </div>

        {/* Use Cases */}
        {model.recommended_for && model.recommended_for.length > 0 && (
          <div className="text-xs text-gray-600 dark:text-gray-400">
            Ideale per: {model.recommended_for.slice(0, 2).join(', ')}
          </div>
        )}
      </div>
    </div>
  )
}