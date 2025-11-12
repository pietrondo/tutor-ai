import { useState, useEffect, useCallback } from 'react'

export interface OpenRouterModel {
  id: string
  name: string
  context_window: number
  max_tokens: number
  description: string
  use_cases: string[]
  cost_per_1k_tokens: {
    input: number
    output: number
  }
  provider: string
  supports_vision: boolean
  category?: string
  display_name?: string
  provider_short?: string
  cost_per_input_1k?: number
  cost_per_output_1k?: number
  total_cost_per_1k?: number
  recommended_for?: string[]
  is_premium?: boolean
  supports_streaming?: boolean
}

export interface ModelFilters {
  search: string
  category: string
  capabilities: string
  min_context: number
}

export interface OpenRouterModelsResponse {
  provider: string | null
  total_models: number
  models: Record<string, OpenRouterModel>
  categories: Record<string, { count: number; description: string }>
  filters_applied: ModelFilters
  current_provider: string
  current_model: string
  connection_status: {
    connected: boolean
    available_models_count?: number
    error?: string
  }
}

export const useOpenRouterModels = () => {
  const [state, setState] = useState<{
    models: Record<string, OpenRouterModel>
    categories: Record<string, { count: number; description: string }>
    totalModels: number
    loading: boolean
    error: string | null
    connectionStatus: { connected: boolean; error?: string }
    filters: ModelFilters
  }>({
    models: {},
    categories: {},
    totalModels: 0,
    loading: false,
    error: null,
    connectionStatus: { connected: false },
    filters: {
      search: '',
      category: 'ALL',
      capabilities: '',
      min_context: 0
    }
  })

  // Fetch models from backend API
  const fetchModels = useCallback(async (filters?: Partial<ModelFilters>) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const params = new URLSearchParams()

      // Always request openrouter provider
      params.append('provider', 'openrouter')

      // Add filters if provided
      if (filters?.search && filters.search.trim()) {
        params.append('search', filters.search.trim())
      }
      if (filters?.category && filters.category !== 'ALL') {
        params.append('category', filters.category)
      }
      if (filters?.capabilities && filters.capabilities.trim()) {
        params.append('capabilities', filters.capabilities.trim())
      }
      if (filters?.min_context && filters.min_context > 0) {
        params.append('min_context', filters.min_context.toString())
      }

      const response = await fetch(`/api/models?${params.toString()}`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data: OpenRouterModelsResponse = await response.json()

      setState(prev => ({
        ...prev,
        models: data.models || {},
        categories: data.categories || {},
        totalModels: data.total_models || 0,
        loading: false,
        error: null,
        connectionStatus: data.connection_status || { connected: false },
        filters: {
          ...prev.filters,
          ...(filters || {})
        }
      }))

      return data
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      console.error('Failed to fetch OpenRouter models:', error)

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
        connectionStatus: { connected: false, error: errorMessage }
      }))

      throw error
    }
  }, [])

  // Update filters
  const updateFilters = useCallback((newFilters: Partial<ModelFilters>) => {
    const updatedFilters = { ...state.filters, ...newFilters }
    setState(prev => ({ ...prev, filters: updatedFilters }))
    return fetchModels(updatedFilters)
  }, [state.filters, fetchModels])

  // Search models
  const searchModels = useCallback((searchTerm: string) => {
    return updateFilters({ search: searchTerm })
  }, [updateFilters])

  // Filter by category
  const filterByCategory = useCallback((category: string) => {
    return updateFilters({ category })
  }, [updateFilters])

  // Filter by capabilities
  const filterByCapabilities = useCallback((capabilities: string) => {
    return updateFilters({ capabilities })
  }, [updateFilters])

  // Filter by minimum context
  const filterByMinContext = useCallback((minContext: number) => {
    return updateFilters({ min_context: minContext })
  }, [updateFilters])

  // Clear all filters
  const clearFilters = useCallback(() => {
    const defaultFilters = {
      search: '',
      category: 'ALL',
      capabilities: '',
      min_context: 0
    }
    setState(prev => ({ ...prev, filters: defaultFilters }))
    return fetchModels(defaultFilters)
  }, [fetchModels])

  // Get model by ID
  const getModel = useCallback((modelId: string): OpenRouterModel | null => {
    return state.models[modelId] || null
  }, [state.models])

  // Get models by category
  const getModelsByCategory = useCallback((category: string): OpenRouterModel[] => {
    return Object.values(state.models).filter(model => model.category === category)
  }, [state.models])

  // Get featured models (first few from recommended category)
  const getFeaturedModels = useCallback((count: number = 3): OpenRouterModel[] => {
    const recommendedModels = Object.values(state.models)
      .filter(model => model.category === 'RECOMMENDED')
      .slice(0, count)

    // If not enough recommended models, add from other categories
    if (recommendedModels.length < count) {
      const otherModels = Object.values(state.models)
        .filter(model => model.category !== 'RECOMMENDED')
        .slice(0, count - recommendedModels.length)
      return [...recommendedModels, ...otherModels]
    }

    return recommendedModels
  }, [state.models])

  // Test model availability
  const testModel = useCallback(async (modelId: string): Promise<boolean> => {
    try {
      const response = await fetch(`/models/openrouter/test`)
      if (!response.ok) return false

      const testData = await response.json()
      return testData.connected
    } catch (error) {
      console.error(`Failed to test model ${modelId}:`, error)
      return false
    }
  }, [])

  // Initial fetch on mount
  useEffect(() => {
    fetchModels()
  }, [])

  return {
    // Data
    models: state.models,
    categories: state.categories,
    totalModels: state.totalModels,

    // State
    loading: state.loading,
    error: state.error,
    connectionStatus: state.connectionStatus,
    filters: state.filters,

    // Actions
    fetchModels,
    updateFilters,
    searchModels,
    filterByCategory,
    filterByCapabilities,
    filterByMinContext,
    clearFilters,

    // Helpers
    getModel,
    getModelsByCategory,
    getFeaturedModels,
    testModel,

    // Computed
    hasModels: Object.keys(state.models).length > 0,
    isConnected: state.connectionStatus.connected,
    availableCategories: Object.keys(state.categories),
  }
}