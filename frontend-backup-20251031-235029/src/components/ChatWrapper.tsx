'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { Send, BookOpen, FileText, Brain, Settings, Zap, Database, Globe, AlertCircle, RefreshCw } from 'lucide-react'
import { ChatMessage } from '@/components/ChatMessage'
import { CourseSelector } from '@/components/CourseSelector'
import { llmManager, LLMRequest, LLMResponse } from '@/lib/llm-manager'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  sources?: Array<{
    source: string
    chunk_index: number
    relevance_score: number
  }>
  provider?: string
  model?: string
  responseTime?: number
  cost?: number
}

interface Course {
  id: string
  name: string
  subject: string
  materials_count: number
}

interface LLMStatus {
  available: boolean
  current: string
  fallbacks: string[]
  totalProviders: number
}

export function ChatWrapper() {
  const searchParams = useSearchParams()
  const [selectedCourse, setSelectedCourse] = useState<string>('')
  const [courses, setCourses] = useState<Course[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null)
  const [showLLMStatus, setShowLLMStatus] = useState(false)
  const [ragEnabled, setRagEnabled] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initializeChat()
  }, [])

  const initializeChat = async () => {
    await loadCourses()
    await checkLLMProviders()

    const courseId = searchParams.get('course')
    if (courseId) {
      setSelectedCourse(courseId)
    }
  }

  const loadCourses = async () => {
    try {
      const response = await fetch('http://localhost:8000/courses')
      const data = await response.json()
      setCourses(data.courses || [])
    } catch (error) {
      console.error('Errore nel caricamento dei corsi:', error)
    }
  }

  const checkLLMProviders = async () => {
    try {
      await llmManager.checkAllProvidersAvailability()
      const availableProviders = llmManager.getAvailableProviders()
      const allProviders = llmManager.getAllProviders()

      setLlmStatus({
        available: availableProviders.length > 0,
        current: availableProviders[0]?.id || 'none',
        fallbacks: availableProviders.slice(1).map(p => p.id),
        totalProviders: allProviders.length
      })
    } catch (error) {
      console.error('Errore nel controllo dei provider LLM:', error)
      setLlmStatus({
        available: false,
        current: 'none',
        fallbacks: [],
        totalProviders: 0
      })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const generateSystemPrompt = (courseContext?: any) => {
    const basePrompt = `Sei un tutor AI esperto per studenti di informatica. Fornisci risposte chiare, accurate e basate sulle migliori pratiche educative.

    Caratteristiche chiave:
    - Sii paziente e incoraggiante
    - Fornisci esempi pratici quando possibile
    - Struttura le risposte in modo logico
    - Adatta la complessità al livello dell'utente
    - Usa un linguaggio chiaro e professionale ma accessibile`

    if (courseContext) {
      return `${basePrompt}

Contesto del corso corrente:
      - Nome: ${courseContext.name}
      - Materia: ${courseContext.subject}
      - Materiali disponibili: ${courseContext.materials_count} documenti
      ${ragEnabled ? 'I materiali del corso sono stati indicizzati e possono essere usati come riferimento per risposte più accurate.' : ''}`
    }

    return basePrompt
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedCourse || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const courseContext = courses.find(c => c.id === selectedCourse)
      const systemPrompt = generateSystemPrompt(courseContext)

      // Perform RAG search if enabled
      let ragContext = null
      if (ragEnabled && courseContext) {
        try {
          const searchResults = await llmManager.searchDocuments(
            input,
            selectedCourse,
            3
          )
          if (searchResults.chunks.length > 0) {
            ragContext = searchResults
          }
        } catch (error) {
          console.error('RAG search failed:', error)
        }
      }

      const llmRequest: LLMRequest = {
        messages: [
          {
            role: 'system',
            content: systemPrompt
          },
          ...messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            ...(ragContext && msg.role === 'assistant' && {
              content: `${msg.content}\n\nFonti RAG: ${ragContext.chunks.length} documenti rilevanti trovati con punteggio di similarità medio di ${(ragContext.chunks.reduce((sum, chunk) => sum + chunk.similarity, 0) / ragContext.chunks.length).toFixed(2)}`
            })
          })),
          {
            role: 'user',
            content: input
          }
        ],
        temperature: 0.7,
        maxTokens: 2000,
        systemPrompt
      }

      const startTime = Date.now()
      const response: LLMResponse = await llmManager.generateResponse(llmRequest)
      const responseTime = Date.now() - startTime

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.content,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        sources: ragContext?.chunks.map((chunk, index) => ({
          source: chunk.source,
          chunk_index: index,
          relevance_score: chunk.similarity
        })),
        provider: response.provider,
        model: response.model,
        responseTime,
        cost: response.cost
      }

      setMessages(prev => [...prev, assistantMessage])
      setSessionId(`session_${Date.now()}`)
    } catch (error) {
      console.error('Errore nell\'invio del messaggio:', error)

      // Determine error type based on error message
      let errorMessage = 'Mi dispiace, si è verificato un errore. Riprova più tardi.'

      if (error instanceof Error) {
        if (error.message.includes('network')) {
          errorMessage = 'Errore di connessione. Verifica la tua connessione internet e riprova.'
        } else if (error.message.includes('API key') || error.message.includes('authentication')) {
          errorMessage = 'Errore di autenticazione. Verifica la configurazione del provider LLM.'
        } else if (error.message.includes('All providers failed')) {
          errorMessage = 'Nessun provider LLM è disponibile. Controlla la configurazione e riprova.'
        }
      }

      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: errorMessage,
        role: 'assistant',
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const selectedCourseData = courses.find(c => c.id === selectedCourse)

  const getLLMStatusIcon = () => {
    if (!llmStatus) return <Globe className="h-5 w-5 text-gray-400" />

    if (llmStatus.available) {
      return <Database className="h-5 w-5 text-green-600" />
    } else {
      return <AlertCircle className="h-5 w-5 text-red-600" />
    }
  }

  const getLLMStatusText = () => {
    if (!llmStatus) return 'Provider sconosciuto'

    if (llmStatus.available) {
      return `${llmStatus.current} disponibile (${llmStatus.fallbacks.length} fallback)`
    } else {
      return `Nessun provider disponibile (${llmStatus.totalProviders} totali)`
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-gray-900">Chat con il Tutor AI Avanzato</h1>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowLLMStatus(!showLLMStatus)}
              className="btn btn-ghost btn-sm"
              title="Stato Provider LLM"
            >
              {getLLMStatusIcon()}
            </button>
            <button
              onClick={() => setRagEnabled(!ragEnabled)}
              className={`btn btn-ghost btn-sm ${ragEnabled ? 'text-green-600' : 'text-gray-600'}`}
              title={ragEnabled ? 'RAG attivo' : 'RAG disattivo'}
            >
              <Database className="h-4 w-4" />
            </button>
          </div>
        </div>
        <p className="text-gray-600">
          Chat intelligente con multi-provider LLM e RAG per risposte accurate basate sui materiali di studio
        </p>
      </div>

      {/* LLM Status Bar */}
      {showLLMStatus && llmStatus && (
        <div className="glass rounded-xl p-4 border border-gray-200/50 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getLLMStatusIcon()}
              <div>
                <div className="text-sm font-medium text-gray-900">Status Provider LLM</div>
                <div className="text-xs text-gray-600">{getLLMStatusText()}</div>
              </div>
            </div>
            <button
              onClick={checkLLMProviders}
              className="btn btn-secondary btn-sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Ricontrolla
            </button>
          </div>

          {llmStatus.available && (
            <div className="mt-3 flex items-center space-x-2 text-xs text-gray-600">
              <span>Provider:</span>
              <span className="font-medium text-gray-900">{llmStatus.current}</span>
              {llmStatus.fallbacks.length > 0 && (
                <>
                  <span>•</span>
                  <span>Fallbacks: {llmStatus.fallbacks.join(', ')}</span>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Course Selector */}
      <div className="mb-6">
        <CourseSelector
          courses={courses}
          selectedCourse={selectedCourse}
          onCourseChange={setSelectedCourse}
        />

        {selectedCourseData && (
          <div className="mt-2 flex items-center text-sm text-gray-600">
            <BookOpen className="h-4 w-4 mr-1" />
            {selectedCourseData.materials_count} materiali disponibili
            {ragEnabled && (
              <>
                <span>•</span>
                <span className="text-green-600">RAG attivo</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Chat Messages */}
      <div className="card mb-6 h-96 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Brain className="h-12 w-12 mb-4 text-gray-400" />
            <h3 className="text-lg font-medium mb-2">Inizia una conversazione intelligente</h3>
            <p className="text-center max-w-md">
              Seleziona un corso e fai la tua domanda al tutor AI avanzato.
              Il sistema utilizerà il provider LLM ottimale e RAG per fornire risposte accurate basate sui materiali caricati.
            </p>
          </div>
        ) : (
          <div className="space-y-4 p-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="loading-spinner"></div>
                <span>Il tutor sta pensando...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Status Indicators */}
      {messages.length > 0 && (
        <div className="mb-4 p-2 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>
              {messages.filter(m => m.role === 'assistant').length} risposte generate
            </span>
            {ragEnabled && (
              <span>• RAG: {messages.filter(m => m.sources && m.sources.length > 0).length} con fonti</span>
            )}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="card">
        <div className="flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={selectedCourse ? "Fai la tua domanda..." : "Seleziona prima un corso..."}
            disabled={!selectedCourse || isLoading}
            className="form-input flex-1"
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || !selectedCourse || isLoading}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isLoading ? (
              <div className="loading-spinner"></div>
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span>Invia</span>
          </button>
        </div>
      </div>

      {/* Features Info */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2 text-blue-800 mb-1">
            <Zap className="h-4 w-4" />
            <span className="font-medium text-sm">Multi-Provider</span>
          </div>
          <p className="text-xs text-blue-700">
            Supporta OpenAI, OpenRouter, LM Studio e altri provider con fallback automatico
          </p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center space-x-2 text-green-800 mb-1">
            <Database className="h-4 w-4" />
            <span className="font-medium text-sm">RAG Integrato</span>
          </div>
          <p className="text-xs text-green-700">
            Ricerca semantica nei documenti per risposte basate sui materiali di studio
          </p>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
          <div className="flex items-center space-x-2 text-purple-800 mb-1">
            <Settings className="h-4 w-4" />
            <span className="font-medium text-sm">Adattivo</span>
          </div>
          <p className="text-xs text-purple-700">
            Selezione automatica del provider ottimale e gestione errori
          </p>
        </div>
      </div>
    </div>
  )
}