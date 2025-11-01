export interface LLMProvider {
  id: string
  name: string
  type: 'openai' | 'openrouter' | 'local' | 'anthropic' | 'cohere'
  apiKey?: string
  baseUrl?: string
  model: string
  maxTokens: number
  temperature: number
  contextWindow: number
  costPerToken?: number
  isAvailable: boolean
  capabilities: {
    streaming: boolean
    functionCalling: boolean
    imageAnalysis: boolean
    codeExecution: boolean
  }
}

export interface LLMRequest {
  messages: Array<{
    role: 'system' | 'user' | 'assistant' | 'function'
    content: string | Array<{
      type: 'text' | 'image_url'
      text?: string
      image_url?: {
        url: string
        detail?: 'low' | 'high'
      }
    }>
    name?: string
    function_call?: any
  }>
  functions?: Array<{
    name: string
    description: string
    parameters: any
  }>
  temperature?: number
  maxTokens?: number
  stream?: boolean
  systemPrompt?: string
}

export interface LLMResponse {
  content: string
  usage?: {
    promptTokens: number
    completionTokens: number
    totalTokens: number
  }
  model: string
  provider: string
  responseTime: number
  cost?: number
}

export interface RAGContext {
  chunks: Array<{
    id: string
    content: string
    source: string
    relevanceScore: number
    metadata?: any
  }>
  totalChunks: number
  searchTime: number
  queryEmbedding?: number[]
}

export interface VectorSearchResult {
  chunks: Array<{
    id: string
    content: string
    similarity: number
    source: string
    metadata: any
  }>
  searchTime: number
  totalResults: number
}

class LLMManager {
  private providers: Map<string, LLMProvider> = new Map()
  private defaultProvider: string = 'openrouter'
  private fallbackChain: string[] = []
  private ragEnabled: boolean = true
  private vectorStore: VectorStore | null = null

  constructor() {
    this.initializeProviders()
    this.initializeVectorStore()
  }

  private initializeProviders() {
    // OpenAI Provider
    this.providers.set('openai', {
      id: 'openai',
      name: 'OpenAI GPT',
      type: 'openai',
      model: 'gpt-4o',
      maxTokens: 4096,
      temperature: 0.7,
      contextWindow: 128000,
      costPerToken: 0.00003,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: false
      }
    })

    // OpenAI GPT-4 Turbo
    this.providers.set('openai-gpt4-turbo', {
      id: 'openai-gpt4-turbo',
      name: 'OpenAI GPT-4 Turbo',
      type: 'openai',
      model: 'gpt-4-turbo',
      maxTokens: 4096,
      temperature: 0.7,
      contextWindow: 128000,
      costPerToken: 0.00003,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: false
      }
    })

    // OpenAI GPT-4
    this.providers.set('openai-gpt4', {
      id: 'openai-gpt4',
      name: 'OpenAI GPT-4',
      type: 'openai',
      model: 'gpt-4',
      maxTokens: 8192,
      temperature: 0.7,
      contextWindow: 8192,
      costPerToken: 0.00006,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: false,
        codeExecution: false
      }
    })

    // OpenAI GPT-3.5 Turbo
    this.providers.set('openai-gpt35-turbo', {
      id: 'openai-gpt35-turbo',
      name: 'OpenAI GPT-3.5 Turbo',
      type: 'openai',
      model: 'gpt-3.5-turbo',
      maxTokens: 4096,
      temperature: 0.7,
      contextWindow: 16385,
      costPerToken: 0.000002,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: false,
        codeExecution: false
      }
    })

    // OpenAI o1 Preview
    this.providers.set('openai-o1-preview', {
      id: 'openai-o1-preview',
      name: 'OpenAI o1 Preview',
      type: 'openai',
      model: 'o1-preview',
      maxTokens: 32768,
      temperature: 1.0, // Fixed temperature for o1 models
      contextWindow: 128000,
      costPerToken: 0.000015,
      isAvailable: false,
      capabilities: {
        streaming: false, // o1 models don't support streaming yet
        functionCalling: false,
        imageAnalysis: false,
        codeExecution: true
      }
    })

    // OpenAI o1 Mini
    this.providers.set('openai-o1-mini', {
      id: 'openai-o1-mini',
      name: 'OpenAI o1 Mini',
      type: 'openai',
      model: 'o1-mini',
      maxTokens: 65536,
      temperature: 1.0, // Fixed temperature for o1 models
      contextWindow: 128000,
      costPerToken: 0.000003,
      isAvailable: false,
      capabilities: {
        streaming: false, // o1 models don't support streaming yet
        functionCalling: false,
        imageAnalysis: false,
        codeExecution: true
      }
    })

    // OpenAI GPT-5 (Latest/Research)
    this.providers.set('openai-gpt5', {
      id: 'openai-gpt5',
      name: 'OpenAI GPT-5',
      type: 'openai',
      model: 'gpt-5',
      maxTokens: 32768,
      temperature: 0.7,
      contextWindow: 200000,
      costPerToken: 0.00008,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: true
      }
    })

    // OpenAI GPT-4.5 (Enhanced)
    this.providers.set('openai-gpt45', {
      id: 'openai-gpt45',
      name: 'OpenAI GPT-4.5 Turbo',
      type: 'openai',
      model: 'gpt-4.5-turbo',
      maxTokens: 16384,
      temperature: 0.7,
      contextWindow: 256000,
      costPerToken: 0.000025,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: true
      }
    })

    // OpenAI GPT-4o Mini (Cost-effective)
    this.providers.set('openai-gpt4o-mini', {
      id: 'openai-gpt4o-mini',
      name: 'OpenAI GPT-4o Mini',
      type: 'openai',
      model: 'gpt-4o-mini',
      maxTokens: 16384,
      temperature: 0.7,
      contextWindow: 128000,
      costPerToken: 0.0000005,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: false
      }
    })

    // OpenAI o1 Pro (Advanced Reasoning)
    this.providers.set('openai-o1-pro', {
      id: 'openai-o1-pro',
      name: 'OpenAI o1 Pro',
      type: 'openai',
      model: 'o1-pro',
      maxTokens: 65536,
      temperature: 1.0, // Fixed temperature for o1 models
      contextWindow: 200000,
      costPerToken: 0.000045,
      isAvailable: false,
      capabilities: {
        streaming: false, // o1 models don't support streaming yet
        functionCalling: false,
        imageAnalysis: false,
        codeExecution: true
      }
    })

    // OpenRouter Provider
    this.providers.set('openrouter', {
      id: 'openrouter',
      name: 'OpenRouter',
      type: 'openrouter',
      baseUrl: 'https://openrouter.ai/api/v1',
      model: 'meta-llama/llama-3.2-3b-instruct:free',
      maxTokens: 4096,
      temperature: 0.7,
      contextWindow: 131072,
      costPerToken: 0.000001,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: false
      }
    })

    // LM Studio Provider
    this.providers.set('lm-studio', {
      id: 'lm-studio',
      name: 'LM Studio',
      type: 'local',
      baseUrl: 'http://localhost:1234/v1',
      model: 'local-model',
      maxTokens: 4096,
      temperature: 0.7,
      contextWindow: 4096,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: false,
        imageAnalysis: false,
        codeExecution: false
      }
    })

    // Ollama Provider
    this.providers.set('ollama', {
      id: 'ollama',
      name: 'Ollama',
      type: 'local',
      baseUrl: 'http://localhost:11434/v1',
      model: 'llama3.2',
      maxTokens: 8192,
      temperature: 0.7,
      contextWindow: 128000,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: false,
        codeExecution: false
      }
    })

    // Anthropic Claude Provider
    this.providers.set('anthropic', {
      id: 'anthropic',
      name: 'Anthropic Claude',
      type: 'anthropic',
      model: 'claude-3-5-sonnet-20241022',
      maxTokens: 4096,
      temperature: 0.7,
      contextWindow: 200000,
      costPerToken: 0.000015,
      isAvailable: false,
      capabilities: {
        streaming: true,
        functionCalling: true,
        imageAnalysis: true,
        codeExecution: false
      }
    })

    // Set fallback chain - prioritize local models, then cost-effective options
    this.fallbackChain = ['ollama', 'lm-studio', 'openrouter', 'openai-gpt4o-mini', 'openai', 'openai-gpt5', 'openai-gpt4-turbo', 'openai-gpt35-turbo', 'openai-o1-mini', 'anthropic']
  }

  private initializeVectorStore() {
    this.vectorStore = new VectorStore()
  }

  async checkProviderAvailability(providerId: string): Promise<boolean> {
    const provider = this.providers.get(providerId)
    if (!provider) return false

    try {
      const baseUrl = provider.baseUrl || this.getDefaultBaseUrl(provider.type)
      if (!baseUrl) {
        console.warn(`No base URL configured for provider ${providerId}`)
        this.providers.get(providerId)!.isAvailable = false
        return false
      }

      // Skip HTTPS check for local providers during development
      const isLocalProvider = provider.type === 'local' || provider.id === 'ollama' || provider.id === 'lm-studio'

      let controller: AbortController | null = new AbortController()
      const timeoutId = setTimeout(() => {
        if (controller) controller.abort()
      }, isLocalProvider ? 3000 : 10000) // Shorter timeout for local providers

      try {
        const response = await fetch(`${baseUrl}/models`, {
          headers: this.getHeaders(provider),
          signal: controller.signal
        })

        clearTimeout(timeoutId)
        controller = null

        const isAvailable = response.ok
        this.providers.get(providerId)!.isAvailable = isAvailable

        if (isAvailable) {
          console.log(`✅ Provider ${providerId} is available at ${baseUrl}`)
        } else {
          console.warn(`⚠️ Provider ${providerId} responded with status ${response.status}`)
        }

        return isAvailable
      } catch (fetchError) {
        clearTimeout(timeoutId)

        if (fetchError.name === 'AbortError') {
          console.warn(`⏰ Provider ${providerId} check timed out`)
        } else if (fetchError.message.includes('Failed to fetch')) {
          console.warn(`🌐 Provider ${providerId} network error - CORS or connection issue`)
        } else {
          console.warn(`❌ Provider ${providerId} fetch error:`, fetchError.message)
        }

        this.providers.get(providerId)!.isAvailable = false
        return false
      }
    } catch (error) {
      console.error(`❌ Provider ${providerId} check failed:`, error)
      this.providers.get(providerId)!.isAvailable = false
      return false
    }
  }

  async checkAllProvidersAvailability(): Promise<void> {
    const promises = Array.from(this.providers.keys()).map(id =>
      this.checkProviderAvailability(id)
    )
    await Promise.allSettled(promises)
  }

  configureProvider(providerId: string, config: Partial<LLMProvider>): void {
    const provider = this.providers.get(providerId)
    if (provider) {
      Object.assign(provider, config)
    }
  }

  setDefaultProvider(providerId: string): void {
    if (this.providers.has(providerId)) {
      this.defaultProvider = providerId
    }
  }

  setFallbackChain(chain: string[]): void {
    this.fallbackChain = chain.filter(id => this.providers.has(id))
  }

  enableRAG(enabled: boolean): void {
    this.ragEnabled = enabled
  }

  private getDefaultBaseUrl(type: LLMProvider['type']): string {
    switch (type) {
      case 'openai':
        return 'https://api.openai.com/v1'
      case 'openrouter':
        return 'https://openrouter.ai/api/v1'
      case 'anthropic':
        return 'https://api.anthropic.com/v1'
      case 'local':
        return 'http://localhost:1234/v1'
      default:
        return ''
    }
  }

  private getHeaders(provider: LLMProvider): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }

    if (provider.apiKey) {
      switch (provider.type) {
        case 'openai':
          headers['Authorization'] = `Bearer ${provider.apiKey}`
          break
        case 'openrouter':
          headers['Authorization'] = `Bearer ${provider.apiKey}`
          headers['HTTP-Referer'] = window.location.origin
          headers['X-Title'] = 'AI Tutor System'
          break
        case 'anthropic':
          headers['x-api-key'] = provider.apiKey
          headers['anthropic-version'] = '2023-06-01'
          break
      }
    }

    return headers
  }

  private async performVectorSearch(query: string, courseId: string, limit: number = 5): Promise<VectorSearchResult> {
    if (!this.vectorStore) {
      return { chunks: [], searchTime: 0, totalResults: 0 }
    }

    const startTime = Date.now()

    try {
      // Generate embedding for query
      const queryEmbedding = await this.generateEmbedding(query)

      // Search vector store
      const results = await this.vectorStore.search(queryEmbedding, courseId, limit)

      return {
        chunks: results,
        searchTime: Date.now() - startTime,
        totalResults: results.length
      }
    } catch (error) {
      console.error('Vector search failed:', error)
      return { chunks: [], searchTime: Date.now() - startTime, totalResults: 0 }
    }
  }

  private async generateEmbedding(text: string): Promise<number[]> {
    // This would call an embedding API (OpenAI, local, etc.)
    // For now, return a mock embedding
    return new Array(1536).fill(0).map(() => Math.random() - 0.5)
  }

  private async callProvider(providerId: string, request: LLMRequest): Promise<LLMResponse> {
    const provider = this.providers.get(providerId)
    if (!provider || !provider.isAvailable) {
      throw new Error(`Provider ${providerId} is not available`)
    }

    const startTime = Date.now()
    const baseUrl = provider.baseUrl || this.getDefaultBaseUrl(provider.type)

    // Add RAG context if enabled
    let enhancedRequest = request
    if (this.ragEnabled && request.messages.length > 0 && request.messages[request.messages.length - 1].role === 'user') {
      const userMessage = request.messages[request.messages.length - 1]
      const ragContext = await this.performVectorSearch(
        typeof userMessage.content === 'string' ? userMessage.content : '',
        'default-course', // This would come from context
        3
      )

      if (ragContext.chunks.length > 0) {
        const contextText = ragContext.chunks
          .map(chunk => chunk.content)
          .join('\n\n')

        enhancedRequest = {
          ...request,
          messages: [
            {
              role: 'system',
              content: `Usa il seguente contesto per rispondere in modo accurato e dettagliato. Se il contesto non è pertinente alla domanda, ignoralo e rispondi normalmente.\n\nContesto rilevante:\n${contextText}`
            },
            ...request.messages.slice(0, -1),
            {
              ...userMessage,
              content: `${userMessage.content}\n\n(Fonti: ${ragContext.chunks.length} documenti rilevanti trovati)`
            }
          ]
        }
      }
    }

    let response: Response

    switch (provider.type) {
      case 'openai':
        response = await this.callOpenAI(baseUrl, enhancedRequest, provider)
        break
      case 'openrouter':
        response = await this.callOpenRouter(baseUrl, enhancedRequest, provider)
        break
      case 'local':
        response = await this.callLocalLLM(baseUrl, enhancedRequest, provider)
        break
      case 'anthropic':
        response = await this.callAnthropic(baseUrl, enhancedRequest, provider)
        break
      default:
        throw new Error(`Unsupported provider type: ${provider.type}`)
    }

    if (!response.ok) {
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    const responseTime = Date.now() - startTime

    return this.parseResponse(data, provider, responseTime)
  }

  private async callOpenAI(baseUrl: string, request: LLMRequest, provider: LLMProvider): Promise<Response> {
    return fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: this.getHeaders(provider),
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        temperature: request.temperature || provider.temperature,
        max_tokens: request.maxTokens || provider.maxTokens,
        stream: request.stream,
        functions: request.functions
      })
    })
  }

  private async callOpenRouter(baseUrl: string, request: LLMRequest, provider: LLMProvider): Promise<Response> {
    return fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: this.getHeaders(provider),
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        temperature: request.temperature || provider.temperature,
        max_tokens: request.maxTokens || provider.maxTokens,
        stream: request.stream,
        functions: request.functions
      })
    })
  }

  private async callLocalLLM(baseUrl: string, request: LLMRequest, provider: LLMProvider): Promise<Response> {
    return fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: this.getHeaders(provider),
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        temperature: request.temperature || provider.temperature,
        max_tokens: request.maxTokens || provider.maxTokens,
        stream: request.stream
      })
    })
  }

  private async callAnthropic(baseUrl: string, request: LLMRequest, provider: LLMProvider): Promise<Response> {
    // Convert OpenAI format to Anthropic format
    const systemMessage = request.messages.find(m => m.role === 'system')
    const messages = request.messages.filter(m => m.role !== 'system')

    return fetch(`${baseUrl}/messages`, {
      method: 'POST',
      headers: this.getHeaders(provider),
      body: JSON.stringify({
        model: provider.model,
        max_tokens: request.maxTokens || provider.maxTokens,
        temperature: request.temperature || provider.temperature,
        system: systemMessage?.content,
        messages: messages.map(m => ({
          role: m.role === 'user' ? 'user' : 'assistant',
          content: typeof m.content === 'string' ? m.content : m.content
        }))
      })
    })
  }

  private parseResponse(data: any, provider: LLMProvider, responseTime: number): LLMResponse {
    let content = ''
    let usage = undefined

    switch (provider.type) {
      case 'openai':
      case 'openrouter':
      case 'local':
        content = data.choices?.[0]?.message?.content || ''
        usage = data.usage
        break
      case 'anthropic':
        content = data.content?.[0]?.text || ''
        usage = {
          promptTokens: data.usage?.input_tokens || 0,
          completionTokens: data.usage?.output_tokens || 0,
          totalTokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0)
        }
        break
    }

    const cost = usage && provider.costPerToken
      ? usage.totalTokens * provider.costPerToken
      : undefined

    return {
      content,
      usage,
      model: provider.model,
      provider: provider.id,
      responseTime,
      cost
    }
  }

  async generateResponse(request: LLMRequest): Promise<LLMResponse> {
    let lastError: Error | null = null

    // Try default provider first
    try {
      if (this.providers.get(this.defaultProvider)?.isAvailable) {
        return await this.callProvider(this.defaultProvider, request)
      }
    } catch (error) {
      lastError = error as Error
      console.warn(`Default provider ${this.defaultProvider} failed:`, error)
    }

    // Try fallback chain
    for (const providerId of this.fallbackChain) {
      if (providerId === this.defaultProvider) continue // Already tried

      try {
        const isAvailable = this.providers.get(providerId)?.isAvailable
        if (isAvailable) {
          console.log(`Falling back to provider: ${providerId}`)
          return await this.callProvider(providerId, request)
        }
      } catch (error) {
        lastError = error as Error
        console.warn(`Fallback provider ${providerId} failed:`, error)
      }
    }

    throw new Error(`All providers failed. Last error: ${lastError?.message}`)
  }

  async generateStreamingResponse(
    request: LLMRequest,
    onChunk: (chunk: string) => void
  ): Promise<LLMResponse> {
    const enhancedRequest = { ...request, stream: true }

    // For now, implement streaming with the first available provider
    // In a full implementation, you'd handle SSE for each provider type
    const response = await this.generateResponse(enhancedRequest)

    // Simulate streaming for demo
    const chunks = response.content.split(' ')
    for (const chunk of chunks) {
      onChunk(chunk + ' ')
      await new Promise(resolve => setTimeout(resolve, 50))
    }

    return response
  }

  getAvailableProviders(): LLMProvider[] {
    return Array.from(this.providers.values()).filter(p => p.isAvailable)
  }

  getAllProviders(): LLMProvider[] {
    return Array.from(this.providers.values())
  }

  getProvider(id: string): LLMProvider | undefined {
    return this.providers.get(id)
  }

  async indexDocument(content: string, metadata: any): Promise<string> {
    if (!this.vectorStore) {
      throw new Error('Vector store not initialized')
    }

    const embedding = await this.generateEmbedding(content)
    return await this.vectorStore.insert(embedding, content, metadata)
  }

  async searchDocuments(query: string, courseId: string, limit: number = 5): Promise<VectorSearchResult> {
    return this.performVectorSearch(query, courseId, limit)
  }

  getProviderStats(): Array<{
    id: string
    name: string
    type: string
    isAvailable: boolean
    model: string
    contextWindow: number
    capabilities: LLMProvider['capabilities']
  }> {
    return Array.from(this.providers.values()).map(provider => ({
      id: provider.id,
      name: provider.name,
      type: provider.type,
      isAvailable: provider.isAvailable,
      model: provider.model,
      contextWindow: provider.contextWindow,
      capabilities: provider.capabilities
    }))
  }
}

// Simplified VectorStore implementation
class VectorStore {
  private documents: Array<{
    id: string
    embedding: number[]
    content: string
    metadata: any
  }> = []

  async insert(embedding: number[], content: string, metadata: any): Promise<string> {
    const id = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    this.documents.push({ id, embedding, content, metadata })
    return id
  }

  async search(queryEmbedding: number[], courseId: string, limit: number): Promise<Array<{
    id: string
    content: string
    similarity: number
    source: string
    metadata: any
  }>> {
    // Simple cosine similarity calculation
    const results = this.documents
      .filter(doc => doc.metadata.courseId === courseId)
      .map(doc => ({
        id: doc.id,
        content: doc.content,
        similarity: this.cosineSimilarity(queryEmbedding, doc.embedding),
        source: doc.metadata.source || 'unknown',
        metadata: doc.metadata
      }))
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit)

    return results
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length) return 0

    let dotProduct = 0
    let normA = 0
    let normB = 0

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i]
      normA += a[i] * a[i]
      normB += b[i] * b[i]
    }

    if (normA === 0 || normB === 0) return 0

    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))
  }
}

export const llmManager = new LLMManager()