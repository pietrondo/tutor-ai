'use client'

import { useState, useEffect, useRef, Suspense, type KeyboardEvent } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Send, Brain, Zap, AlertCircle, RefreshCw, MessageSquare, BookOpen, Target } from 'lucide-react'
import { ChatMessage } from '@/components/ChatMessage'

interface Course {
  id: string
  name: string
  subject: string
  description: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
}

interface Book {
  id: string
  title: string
  author: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
  chapters: Array<{
    title: string
    summary: string
    estimated_minutes: number | null
    topics: string[]
  }>
  tags: string[]
}

interface SessionMessage {
  id: string
  timestamp: string
  role: 'user' | 'assistant'
  content: string
  sources: Array<{
    source: string
    chunk_index: number
    content: string
    relevance_score: number
    source_type: string
    book_title?: string
  }>
  context_used: string[]
  confidence_score: number
  topic_tags: string[]
  response_time_ms: number
  is_followup: boolean
  parent_message_id?: string
}

interface CourseSession {
  id: string
  course_id: string
  created_at: string
  last_activity: string
  messages: SessionMessage[]
  context: {
    topic_history: any
    concept_map: any
    study_progress: any
    learning_style: any
    difficulty_level: any
  }
  metadata: {
    device_type: string
    preferred_response_length: string
    verbosity_level: string
    language: string
  }
  statistics: {
    total_messages: number
    user_messages: number
    assistant_messages: number
    total_response_time_ms: number
    average_confidence: number
    topics_discussed: string[]
    concepts_covered: string[]
    sources_used: string[]
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8001'

function CourseChatContent() {
  const params = useParams()
  const courseId = params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [currentSession, setCurrentSession] = useState<CourseSession | null>(null)
  const [sessions, setSessions] = useState<CourseSession[]>([])
  const [books, setBooks] = useState<Book[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [courseLoading, setCourseLoading] = useState(true)
  const [sessionLoading, setSessionLoading] = useState(true)
  const [showSessionHistory, setShowSessionHistory] = useState(false)
  const [error, setError] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (courseId) {
      loadCourse()
      loadSessions()
    }
  }, [courseId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentSession?.messages])

  const loadCourse = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}`)
      const data = await response.json()

      if (response.ok) {
        setCourse(data.course)
        await loadBooks(courseId)
      } else {
        setError('Corso non trovato')
      }
    } catch (error) {
      console.error('Errore nel caricamento del corso:', error)
      setError('Errore di connessione al server')
    } finally {
      setCourseLoading(false)
    }
  }

  const loadBooks = async (courseId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}/books`)
      if (response.ok) {
        const data = await response.json()
        setBooks(data.books || [])
      }
    } catch (error) {
      console.error('Errore nel caricamento dei libri:', error)
    }
  }

  const loadSessions = async () => {
    setSessionLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/course-chat/${courseId}/sessions`)
      if (response.ok) {
        const data = await response.json()
        setSessions(data.sessions || [])

        // Get or create current session
        if (data.sessions.length > 0) {
          // Use the most recent session
          const recentSession = data.sessions.reduce((latest: CourseSession, session: CourseSession) =>
            new Date(session.last_activity) > new Date(latest.last_activity) ? session : latest
          )
          loadSession(recentSession.id)
        } else {
          // Create new session
          createNewSession()
        }
      } else {
        // Create new session if none exist
        createNewSession()
      }
    } catch (error) {
      console.error('Errore nel caricamento delle sessioni:', error)
      // Try to create new session anyway
      createNewSession()
    } finally {
      setSessionLoading(false)
    }
  }

  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/course-chat/${courseId}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })

      if (response.ok) {
        const data = await response.json()
        loadSession(data.session.id)
        setSessions(prev => [data.session, ...prev])
      }
    } catch (error) {
      console.error('Errore nella creazione della sessione:', error)
    }
  }

  const loadSession = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/course-chat/session/${sessionId}`)
      if (response.ok) {
        const data = await response.json()
        setCurrentSession(data.session)
      }
    } catch (error) {
      console.error('Errore nel caricamento della sessione:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || !currentSession || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/course-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          session_id: currentSession.id,
          message: userMessage,
          context_updates: {
            preferred_response_length: 'medium',
            verbosity_level: 'detailed'
          }
        })
      })

      if (response.ok) {
        const data = await response.json()

        // Update current session with new messages
        if (data.session && data.session.messages) {
          setCurrentSession(data.session)

          // Update session in sessions list
          setSessions(prev => prev.map(session =>
            session.id === data.session.id ? data.session : session
          ))
        }
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nell\'invio del messaggio')
      }
    } catch (error) {
      console.error('Errore nell\'invio del messaggio:', error)

      // Add error message to chat
      const errorMessage: SessionMessage = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        role: 'assistant',
        content: 'Mi dispiace, si è verificato un errore. Riprova più tardi.',
        sources: [],
        context_used: [],
        confidence_score: 0,
        topic_tags: [],
        response_time_ms: 0,
        is_followup: false
      }

      setCurrentSession(prev => prev ? {
        ...prev,
        messages: [...prev.messages, errorMessage]
      } : null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const switchSession = (sessionId: string) => {
    loadSession(sessionId)
    setShowSessionHistory(false)
  }

  const clearCurrentSession = () => {
    if (currentSession) {
      setCurrentSession({
        ...currentSession,
        messages: []
      })
    }
  }

  if (courseLoading || sessionLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {error || 'Corso non trovato'}
        </h2>
        <Link href="/courses" className="btn btn-primary">
          Torna ai Corsi
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Link
            href={`/courses/${courseId}`}
            className="inline-flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna al Corso
          </Link>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowSessionHistory(!showSessionHistory)}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Sessioni ({sessions.length})</span>
            </button>

            {currentSession && (
              <button
                onClick={clearCurrentSession}
                className="text-gray-600 hover:text-gray-800 text-sm"
              >
                Svuota chat
              </button>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-1">Tutor AI del Corso</h1>
              <p className="text-lg text-gray-600">{course.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {books.length} libri disponibili • {course.materials_count} materiali indicizzati
              </p>
            </div>

            {currentSession && (
              <div className="text-right">
                <div className="text-sm text-gray-500">
                  Sessione attiva
                </div>
                <div className="text-xs text-gray-400">
                  {currentSession.statistics.total_messages} messaggi
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Session History Sidebar */}
      {showSessionHistory && (
        <div className="mb-6 bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cronologia Sessioni</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {sessions.map(session => (
              <button
                key={session.id}
                onClick={() => switchSession(session.id)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  currentSession?.id === session.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {new Date(session.created_at).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {session.statistics.total_messages} messaggi
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(session.last_activity).toLocaleTimeString()}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="bg-white rounded-lg border border-gray-200 min-h-[500px] max-h-[600px] flex flex-col">
        <div className="flex-1 overflow-y-auto p-6">
          {!currentSession || currentSession.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
              <Brain className="h-12 w-12 text-blue-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Inizia a conversare</h3>
              <p className="text-sm">
                Sono il tuo tutor AI personale per questo corso.
                Fammi domande sui contenuti, chiedi spiegazioni o esercizi.
              </p>
              {books.length === 0 && (
                <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <p className="text-xs text-amber-800">
                    Nessun materiale indicizzato. Carica alcuni libri per ottenere risposte più precise.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {currentSession.messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Sto pensando...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4">
          <div className="flex space-x-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Fai la tua domanda al tutor AI..."
              disabled={isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span>Invia</span>
            </button>
          </div>

          {currentSession && (
            <div className="mt-2 text-xs text-gray-500">
              Confidence media: {(currentSession.statistics.average_confidence * 100).toFixed(0)}% •
              Tempi discussi: {currentSession.statistics.topics_discussed.length}
            </div>
          )}
        </div>
      </div>

      {/* Course Info */}
      {books.length > 0 && (
        <div className="mt-6 bg-blue-50 rounded-lg border border-blue-200 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <BookOpen className="h-5 w-5 text-blue-600" />
            <h3 className="text-sm font-medium text-blue-900">Materiali disponibili</h3>
          </div>
          <div className="text-xs text-blue-700">
            {books.slice(0, 3).map(book => book.title).join(', ')}
            {books.length > 3 && ` e altri ${books.length - 3} libri`}
          </div>
        </div>
      )}
    </div>
  )
}

export default function CourseChatPage() {
  return (
    <Suspense fallback={
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    }>
      <CourseChatContent />
    </Suspense>
  )
}
