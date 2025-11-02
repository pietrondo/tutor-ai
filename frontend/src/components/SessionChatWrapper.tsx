'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Send, ArrowLeft, BookOpen, Target, Clock, CheckCircle, AlertCircle, Brain, Map, MessageSquare } from 'lucide-react'
import { ChatMessage } from '@/components/ChatMessage'
import { MindMapViewer } from '@/components/MindMapViewer'
import { llmManager, LLMRequest, LLMResponse } from '@/lib/llm-manager'
import { MindMap } from '@/types/mindmap'

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

interface SessionChatWrapperProps {
  sessionId: string
  planId: string
  courseId: string
  sessionTitle: string
}

interface StudySession {
  id: string
  title: string
  description: string
  duration_minutes: number
  topics: string[]
  materials: string[]
  difficulty: string
  objectives: string[]
  prerequisites: string[]
  completed: boolean
  order_index: number
}

export function SessionChatWrapper({ sessionId, planId, courseId, sessionTitle }: SessionChatWrapperProps) {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [session, setSession] = useState<StudySession | null>(null)
  const [ragEnabled, setRagEnabled] = useState(true)
  const [showMindMap, setShowMindMap] = useState(false)
  const [mindMap, setMindMap] = useState<MindMap | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessionData()
    loadChatHistory()
  }, [sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadSessionData = async () => {
    try {
      // In a real app, you'd fetch this from the API
      // For now, we'll use the sessionTitle and courseId to create context
      setSession({
        id: sessionId,
        title: sessionTitle,
        description: 'Sessione di studio personalizzata',
        duration_minutes: 45,
        topics: [], // Would be populated from API
        materials: [], // Would be populated from API
        difficulty: 'intermediate',
        objectives: [], // Would be populated from API
        prerequisites: [], // Would be populated from API
        completed: false,
        order_index: 0
      })
    } catch (error) {
      console.error('Error loading session data:', error)
    }
  }

  const loadChatHistory = async () => {
    try {
      // Load chat history from localStorage or API
      const savedMessages = localStorage.getItem(`chat_session_${sessionId}`)
      if (savedMessages) {
        setMessages(JSON.parse(savedMessages))
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
    }
  }

  const loadMindMap = async () => {
    try {
      // Load mind map from localStorage
      const savedMindMap = localStorage.getItem(`mindmap_session_${sessionId}`)
      if (savedMindMap) {
        setMindMap(JSON.parse(savedMindMap))
      } else {
        // Create initial mind map structure
        const initialMindMap: MindMap = {
          id: `mindmap-${sessionId}`,
          sessionId: sessionId,
          title: sessionTitle,
          description: `Mappa concettuale per: ${sessionTitle}`,
          nodes: [],
          edges: [],
          metadata: {
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            version: '1.0.0',
            author: 'Student',
            tags: ['study', 'concept-map'],
            difficulty: 'intermediate' as const,
            sessionTitle: sessionTitle,
            courseId: courseId
          },
          layout: {
            type: 'mindmap',
            nodeSpacing: 100,
            levelSpacing: 150,
            direction: 'TB'
          },
          style: {
            theme: 'colorful',
            nodeBaseSize: 1,
            edgeBaseSize: 1
          }
        }
        setMindMap(initialMindMap)
      }
    } catch (error) {
      console.error('Error loading mind map:', error)
    }
  }

  useEffect(() => {
    if (session) {
      loadMindMap()
    }
  }, [session, sessionId])

  const saveChatHistory = (newMessages: Message[]) => {
    try {
      localStorage.setItem(`chat_session_${sessionId}`, JSON.stringify(newMessages))
    } catch (error) {
      console.error('Error saving chat history:', error)
    }
  }

  const handleMindMapChange = (updatedMindMap: MindMap) => {
    setMindMap(updatedMindMap)
    try {
      localStorage.setItem(`mindmap_session_${sessionId}`, JSON.stringify(updatedMindMap))
    } catch (error) {
      console.error('Error saving mind map:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const generateSystemPrompt = () => {
    if (!session) return ''

    return `
Sei un tutor esperto specializzato per questa sessione di studio specifica.

CONTESTO DELLA SESSIONE:
- Titolo: ${session.title}
- Descrizione: ${session.description}
- Durata: ${session.duration_minutes} minuti
- Difficoltà: ${session.difficulty}
- Obiettivi: ${session.objectives.length > 0 ? session.objectives.join(', ') : 'Non specificati'}
- Prerequisiti: ${session.prerequisites.length > 0 ? session.prerequisites.join(', ') : 'Non specificati'}

COMPITI:
1. Aiuta lo studente a comprendere gli argomenti di questa sessione
2. Fornisci spiegazioni chiare e dettagliate
3. Suggerisci esercizi pratici se appropriato
4. Adatta le risposte al livello di difficoltà: ${session.difficulty}
5. Concentrati sugli obiettivi di apprendimento specifici
6. Usa il contesto del corso (${courseId}) per fornire risposte pertinenti

Rispondi sempre in italiano e sii incoraggiante e paziente.
    `.trim()
  }

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date().toISOString()
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    saveChatHistory(newMessages)
    setInput('')
    setIsLoading(true)

    try {
      const systemPrompt = generateSystemPrompt()

      // Perform RAG search if enabled
      let ragContext = null
      if (ragEnabled && courseId) {
        try {
          const searchResults = await llmManager.searchDocuments(
            input,
            courseId,
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
              sources: ragContext.chunks.map((chunk: any) => ({
                source: chunk.source || 'Documento',
                chunk_index: chunk.chunk_index || 0,
                relevance_score: chunk.relevance_score || 0.8
              }))
            })
          })),
          {
            role: 'user',
            content: input,
            ...(ragContext && {
              sources: ragContext.chunks.map((chunk: any) => ({
                source: chunk.source || 'Documento',
                chunk_index: chunk.chunk_index || 0,
                relevance_score: chunk.relevance_score || 0.8
              }))
            })
          }
        ]
      }

      const response = await llmManager.generateResponse(llmRequest)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.content,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        sources: ragContext?.chunks.map((chunk: any) => ({
          source: chunk.source || 'Documento',
          chunk_index: chunk.chunk_index || 0,
          relevance_score: chunk.relevance_score || 0.8
        })),
        provider: response.provider,
        model: response.model,
        responseTime: response.responseTime,
        cost: response.cost
      }

      const finalMessages = [...newMessages, assistantMessage]
      setMessages(finalMessages)
      saveChatHistory(finalMessages)
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Mi dispiace, ho riscontrato un errore. Per favore riprova più tardi.',
        role: 'assistant',
        timestamp: new Date().toISOString()
      }
      const errorMessages = [...newMessages, errorMessage]
      setMessages(errorMessages)
      saveChatHistory(errorMessages)
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

  const clearChat = () => {
    setMessages([])
    localStorage.removeItem(`chat_session_${sessionId}`)
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-16">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Caricamento sessione...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.back()}
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Torna ai Piani</span>
            </button>
            <div className="h-6 w-px bg-gray-300"></div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{session.title}</h1>
              <p className="text-gray-600">
                {showMindMap ? 'Mappa concettuale interattiva' : 'Chat dedicata per questa sessione'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {/* View Toggle Buttons */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setShowMindMap(false)}
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  !showMindMap
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <MessageSquare className="h-4 w-4" />
                <span>Chat</span>
              </button>
              <button
                onClick={() => setShowMindMap(true)}
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  showMindMap
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Map className="h-4 w-4" />
                <span>Mappa</span>
              </button>
            </div>

            <div className="h-4 w-px bg-gray-300"></div>

            <button
              onClick={() => setRagEnabled(!ragEnabled)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                ragEnabled
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              RAG: {ragEnabled ? 'ON' : 'OFF'}
            </button>
            <button
              onClick={clearChat}
              className="px-3 py-1 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 text-sm font-medium transition-colors"
            >
              Pulisci Chat
            </button>
          </div>
        </div>

        {/* Session Info Bar */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <BookOpen className="h-4 w-4 text-blue-600" />
                <span className="font-medium text-blue-900">Sessione {session.order_index + 1}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-blue-600" />
                <span className="text-blue-700">{session.duration_minutes} minuti</span>
              </div>
              <div className="flex items-center space-x-2">
                <Target className="h-4 w-4 text-blue-600" />
                <span className="text-blue-700">{session.difficulty}</span>
              </div>
              {session.completed && (
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-green-700 font-medium">Completata</span>
                </div>
              )}
            </div>
            {session.objectives.length > 0 && (
              <div className="text-sm text-blue-700">
                <strong>Obiettivi:</strong> {session.objectives.length} obiettivi
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {showMindMap ? (
        /* Mind Map View */
        <div className="bg-white rounded-lg border border-gray-200 mb-6">
          {mindMap ? (
            <MindMapViewer
              mindMap={mindMap}
              onMindMapChange={handleMindMapChange}
              readOnly={false}
              enableEditing={true}
              className="h-[600px]"
            />
          ) : (
            <div className="flex items-center justify-center h-[600px] text-gray-500">
              <div className="text-center">
                <div className="loading-spinner mx-auto mb-4"></div>
                <p>Caricamento mappa concettuale...</p>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Chat View */
        <>
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6 h-96 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <Brain className="h-12 w-12 mb-4 text-gray-400" />
                <h3 className="text-lg font-medium mb-2">Inizia la sessione di studio</h3>
                <p className="text-center max-w-md">
                  Sono qui per aiutarti con questa sessione di studio.
                  Fammi domande sugli argomenti, chiedi spiegazioni o esercizi pratici.
                </p>
                {ragEnabled && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-sm text-green-800">
                      <AlertCircle className="inline h-4 w-4 mr-1" />
                      RAG è attivo: userò i materiali del corso per darti risposte precise
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input - Only show in chat view */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center space-x-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Fai una domanda su questa sessione..."
                disabled={isLoading}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={handleSendMessage}
                disabled={!input.trim() || isLoading}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
              >
                {isLoading ? (
                  <div className="loading-spinner"></div>
                ) : (
                  <Send className="h-4 w-4" />
                )}
                <span>Invia</span>
              </button>
            </div>

            {/* Session Context Hints */}
            {session.objectives.length > 0 && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Obiettivi della sessione:</strong>
                </p>
                <div className="flex flex-wrap gap-2">
                  {session.objectives.map((objective, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                      {objective}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {session.topics.length > 0 && (
              <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Argomenti principali:</strong>
                </p>
                <div className="flex flex-wrap gap-2">
                  {session.topics.map((topic, index) => (
                    <span key={index} className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      </div>
  )
}