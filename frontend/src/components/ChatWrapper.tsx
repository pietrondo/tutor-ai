'use client'

import {
  useState,
  useEffect,
  useRef,
  useMemo,
  type KeyboardEventHandler,
  type FormEvent
} from 'react'
import { useSearchParams } from 'next/navigation'
import {
  Send,
  Brain,
  Zap,
  AlertCircle,
  RefreshCw,
  Filter,
  Target
} from 'lucide-react'
import { ChatMessage } from '@/components/ChatMessage'
import { CourseSelector } from '@/components/CourseSelector'
import BookSelector from '@/components/BookSelector'
import { ConceptVisualMap } from '@/components/ConceptVisualMap'
import { llmManager, LLMRequest, LLMResponse } from '@/lib/llm-manager'
import type { CourseConcept, ConceptMetrics, CourseConceptMap } from '@/types/concept'

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

interface Book {
  id: string
  title: string
  author?: string
  materials_count: number
}

interface LLMStatus {
  available: boolean
  current: string
  fallbacks: string[]
  totalProviders: number
}

interface QuizQuestion {
  question: string
  options: Record<string, string>
  correct: string
  explanation: string
}

interface ConceptQuiz {
  title: string
  difficulty: string
  questions: QuizQuestion[]
}

interface ActiveQuizState {
  concept: CourseConcept
  quiz: ConceptQuiz
  answers: Record<number, string>
  startTime: number
  submitted: boolean
  result?: {
    score: number
    correct: number
    total: number
    timeSeconds: number
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8001'
const MAX_FOCUS_CONCEPTS = 3

export function ChatWrapper() {
  const searchParams = useSearchParams()
  const [selectedCourse, setSelectedCourse] = useState('')
  const [selectedBook, setSelectedBook] = useState('')
  const [courses, setCourses] = useState<Course[]>([])
  const [books, setBooks] = useState<Book[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null)
  const [showLLMStatus, setShowLLMStatus] = useState(false)
  const [ragEnabled, setRagEnabled] = useState(true)

  const [conceptMap, setConceptMap] = useState<CourseConceptMap | null>(null)
  const [conceptMetrics, setConceptMetrics] = useState<ConceptMetrics>({})
  const [conceptsLoading, setConceptsLoading] = useState(false)
  const [conceptError, setConceptError] = useState<string | null>(null)
  const [conceptsGenerating, setConceptsGenerating] = useState(false)
  const [conceptProgress, setConceptProgress] = useState(0)
  const [selectedConceptIds, setSelectedConceptIds] = useState<string[]>([])
  const [activeQuiz, setActiveQuiz] = useState<ActiveQuizState | null>(null)
  const [showConceptMap, setShowConceptMap] = useState(true)
  const [mentionedConcepts, setMentionedConcepts] = useState<string[]>([])

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initializeChat()
  }, [])

  useEffect(() => {
    if (selectedCourse) {
      loadBooks(selectedCourse)
      loadConceptContext(selectedCourse)
    } else {
      setBooks([])
      setSelectedBook('')
      setConceptMap(null)
      setConceptMetrics({})
      setSelectedConceptIds([])
    }
  }, [selectedCourse])

  const initializeChat = async () => {
    await loadCourses()
    await loadSavedSettings()
    await checkLLMProviders()

    const courseId = searchParams.get('course')
    const bookId = searchParams.get('book')

    if (courseId) {
      setSelectedCourse(courseId)
      await loadBooks(courseId)
      await loadConceptContext(courseId)
    }

    if (bookId) {
      setSelectedBook(bookId)
    }
  }

  const loadSavedSettings = async () => {
    try {
      const savedApiKeys = localStorage.getItem('api-keys')
      const savedSettings = localStorage.getItem('app-settings')

      if (savedApiKeys) {
        const apiKeys = JSON.parse(savedApiKeys)

        if (apiKeys.openai) {
          llmManager.configureProvider('openai', { apiKey: apiKeys.openai })
        }

        if (apiKeys.openrouter) {
          llmManager.configureProvider('openrouter', { apiKey: apiKeys.openrouter })
        }

        if (apiKeys.anthropic) {
          llmManager.configureProvider('anthropic', { apiKey: apiKeys.anthropic })
        }

        if (apiKeys.zai) {
          llmManager.configureProvider('zai', { apiKey: apiKeys.zai })
        }

        if (savedSettings) {
          const settings = JSON.parse(savedSettings)
          if (settings.llmProvider && apiKeys[settings.llmProvider]) {
            llmManager.setDefaultProvider(settings.llmProvider)
          }
        }
      }
    } catch (error) {
      console.error('Error loading saved settings:', error)
    }
  }

  const loadCourses = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses`)
      const data = await response.json()
      setCourses(data.courses || [])
    } catch (error) {
      console.error('Errore nel caricamento dei corsi:', error)
    }
  }

  const loadBooks = async (courseId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}/books`)
      const data = await response.json()
      setBooks(data.books || [])
    } catch (error) {
      console.error('Errore nel caricamento dei libri:', error)
    }
  }

  const loadConceptContext = async (courseId: string) => {
    setConceptsLoading(true)
    setConceptError(null)
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}/concepts`)
      if (response.ok) {
        const data = await response.json()
        setConceptMap(data.concept_map)
        await loadConceptMetrics(courseId)
      } else if (response.status === 404) {
        setConceptMap(null)
        setConceptMetrics({})
      } else {
        throw new Error('Impossibile caricare la mappa concettuale')
      }
    } catch (error) {
      console.error('Errore concept map:', error)
      setConceptError('Nessuna mappa concettuale disponibile. Generala per iniziare.')
      setConceptMap(null)
      setConceptMetrics({})
    } finally {
      setConceptsLoading(false)
    }
  }

  const loadConceptMetrics = async (courseId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}/concepts/metrics`)
      if (response.ok) {
        const data = await response.json()
        setConceptMetrics(data.metrics || {})
      }
    } catch (error) {
      console.error('Errore caricamento metriche concetti:', error)
    }
  }

  const handleGenerateConceptMap = async () => {
    if (!selectedCourse) return

    setConceptsGenerating(true)
    setConceptError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/courses/${selectedCourse}/concepts/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(90000),
        body: JSON.stringify({ book_id: selectedBook || undefined, force: true })
      })

      if (!response.ok) {
        let detail = 'Errore generazione concept map'
        try {
          const errorData = await response.json()
          if (typeof errorData?.detail === 'string') {
            detail = errorData.detail
          }
        } catch {
          // Ignore JSON parsing errors for non-JSON responses
        }
        throw new Error(detail)
      }

      const data = await response.json()
      setConceptMap(data.concept_map)
      setSelectedConceptIds([])
      await loadConceptMetrics(selectedCourse)
      setConceptProgress(100)
    } catch (error) {
      console.error('Errore generazione concept map:', error)

      const fallbackMessage = 'Impossibile generare la mappa concettuale. Riprova più tardi.'
      let message = fallbackMessage

      if (error instanceof DOMException && error.name === 'TimeoutError') {
        message = 'La generazione sta impiegando troppo tempo. Controlla che il backend sia attivo e riprova.'
      } else if (error instanceof Error) {
        message = error.message || fallbackMessage
      }

      if (message.toLowerCase().includes('nessun materiale')) {
        message = 'Non sono stati indicizzati materiali per questo corso. Carica o reindicizza i contenuti prima di generare la mappa.'
      }

      setConceptError(message)
      setConceptMap(null)
      setConceptMetrics({})
    } finally {
      setConceptsGenerating(false)
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
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!conceptsGenerating) {
      return
    }

    setConceptProgress(8)
    const interval = setInterval(() => {
      setConceptProgress(prev => {
        if (prev >= 92) {
          return prev
        }
        const increment = Math.random() * 9 + 3
        return Math.min(prev + increment, 92)
      })
    }, 1500)

    return () => {
      clearInterval(interval)
    }
  }, [conceptsGenerating])

  useEffect(() => {
    if (!conceptsGenerating && conceptProgress > 0) {
      const timeout = setTimeout(() => setConceptProgress(0), 600)
      return () => clearTimeout(timeout)
    }
  }, [conceptsGenerating, conceptProgress])

  const selectedCourseData = useMemo(
    () => courses.find(c => c.id === selectedCourse) || null,
    [courses, selectedCourse]
  )

  const selectedBookData = useMemo(
    () => books.find(b => b.id === selectedBook) || null,
    [books, selectedBook]
  )

  const selectedConcepts = useMemo(
    () => (conceptMap?.concepts || []).filter(concept => selectedConceptIds.includes(concept.id)),
    [conceptMap, selectedConceptIds]
  )

  // Funzione per estrarre concetti menzionati nelle risposte AI
  const extractConceptsFromResponse = (response: string) => {
    if (!conceptMap?.concepts) return

    const concepts = conceptMap.concepts
    const mentioned: string[] = []

    concepts.forEach(concept => {
      // Cerca menzioni dirette del nome del concetto
      if (response.toLowerCase().includes(concept.name.toLowerCase())) {
        mentioned.push(concept.id)
      }

      // Cerca menzioni di parole chiave correlate
      const keywords = [...concept.related_topics, ...concept.learning_objectives]
      keywords.forEach(keyword => {
        if (response.toLowerCase().includes(keyword.toLowerCase()) && !mentioned.includes(concept.id)) {
          mentioned.push(concept.id)
        }
      })
    })

    if (mentioned.length > 0) {
      setMentionedConcepts(prev => [...new Set([...prev, ...mentioned])])
    }
  }

  // Funzione per espandere automaticamente i concetti correlati
  const expandRelatedConcepts = (mainConcepts: string[]) => {
    if (!conceptMap?.concepts) return

    const relatedIds = new Set<string>()

    conceptMap.concepts.forEach(concept => {
      if (mainConcepts.includes(concept.id)) {
        // Aggiungi il concetto principale
        relatedIds.add(concept.id)

        // Aggiungi concetti correlati
        concept.related_topics.forEach(topic => {
          const relatedConcept = conceptMap.concepts.find(c =>
            c.name.toLowerCase().includes(topic.toLowerCase()) ||
            c.related_topics.some(rt => rt.toLowerCase() === topic.toLowerCase())
          )
          if (relatedConcept) {
            relatedIds.add(relatedConcept.id)
          }
        })
      }
    })

    setSelectedConceptIds(prev => [...new Set([...prev, ...Array.from(relatedIds).slice(0, MAX_FOCUS_CONCEPTS)])])
  }

  const toggleConcept = (conceptId: string) => {
    setSelectedConceptIds(prev => {
      if (prev.includes(conceptId)) {
        return prev.filter(id => id !== conceptId)
      }
      if (prev.length >= MAX_FOCUS_CONCEPTS) {
        const [, ...rest] = [...prev, conceptId]
        return rest
      }
      return [...prev, conceptId]
    })
  }

  const generateSystemPrompt = (courseContext?: Course, bookContext?: Book) => {
    const basePrompt = `Sei un tutor AI esperto per studenti universitari. Fornisci risposte chiare, accurate e pratiche.

Caratteristiche chiave:
- Sii paziente e incoraggiante
- Fornisci esempi pratici quando possibile
- Struttura le risposte in modo logico
- Adatta la complessità al livello dell'utente
- Usa un linguaggio chiaro e professionale ma accessibile`

    let contextInfo = ''

    if (courseContext) {
      contextInfo += `\nContesto del corso:\n- Nome: ${courseContext.name}\n- Materia: ${courseContext.subject}\n- Materiali indicizzati: ${courseContext.materials_count}`
    }

    if (bookContext) {
      contextInfo += `\nMateriale in focus: ${bookContext.title}${bookContext.author ? ` (${bookContext.author})` : ''}`
    }

    if (selectedConcepts.length > 0) {
      const conceptSummaries = selectedConcepts.map(concept => {
        const metrics = conceptMetrics[concept.id]
        const statsText = metrics
          ? `, performance media quizzes: ${(metrics.stats.average_score * 100).toFixed(0)}%`
          : ''
        return `- ${concept.name} (Capitolo: ${concept.chapter?.title || 'N/A'}${statsText})\n  Obiettivi: ${concept.learning_objectives.slice(0, 2).join('; ')}`
      }).join('\n')
      contextInfo += `\nConcetti prioritari:\n${conceptSummaries}`
    }

    if (!contextInfo) {
      return basePrompt
    }

    return `${basePrompt}\n\n${contextInfo}`
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedCourse) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      role: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const courseContext = selectedCourseData || undefined
    const bookContext = selectedBookData || undefined
    const systemPrompt = generateSystemPrompt(courseContext, bookContext)

    const llmRequest: LLMRequest = {
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages.map((message) => ({ role: message.role, content: message.content })),
        { role: 'user', content: userMessage.content }
      ],
      rag_enabled: ragEnabled,
      course_id: selectedCourse,
      metadata: {
        book_id: selectedBook || undefined,
        focus_concepts: selectedConcepts.map(concept => ({
          id: concept.id,
          name: concept.name,
          chapter: concept.chapter?.title
        }))
      }
    }

    const startTime = performance.now()

    try {
      const response: LLMResponse = await llmManager.invoke(llmRequest)
      const responseTime = performance.now() - startTime
      const normalizedSources = (response.sources ?? []).map((chunk, index) => {
        const chunkRecord = chunk as Record<string, unknown>
        const rawSource = chunkRecord.source
        const rawSimilarity = chunkRecord.similarity
        const rawScore = chunkRecord.score
        const rawRelevance = chunkRecord.relevance_score
        const source =
          typeof rawSource === 'string'
            ? rawSource
            : rawSource !== undefined && rawSource !== null
              ? String(rawSource)
              : `Fonte ${index + 1}`
        const relevance =
          typeof rawSimilarity === 'number'
            ? rawSimilarity
            : typeof rawRelevance === 'number'
              ? rawRelevance
              : typeof rawScore === 'number'
                ? rawScore
                : 0.75
        return {
          source,
          chunk_index: index,
          relevance_score: relevance
        }
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.message ?? response.content,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        sources: normalizedSources,
        provider: response.provider,
        model: response.model,
        responseTime,
        cost: response.cost
      }

      setMessages(prev => [...prev, assistantMessage])

      // Estrai concetti dalla risposta AI e espandi automaticamente
      extractConceptsFromResponse(assistantMessage.content)

      // Se ci sono concetti selezionati, espandi anche quelli correlati
      if (selectedConcepts.length > 0) {
        expandRelatedConcepts(selectedConcepts.map(c => c.id))
      }
    } catch (error) {
      console.error('Errore nell\'invio del messaggio:', error)

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

  const handleKeyPress: KeyboardEventHandler<HTMLInputElement> = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  const handleStartQuiz = async (concept: CourseConcept) => {
    if (!selectedCourse) return

    setActiveQuiz(null)
    try {
      const response = await fetch(`${API_BASE_URL}/quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: selectedCourse,
          topic: concept.name,
          difficulty: 'medium',
          num_questions: 5
        })
      })

      if (!response.ok) {
        throw new Error('Errore generazione quiz')
      }

      const data = await response.json()
      const quiz: ConceptQuiz = data.quiz
      setActiveQuiz({
        concept,
        quiz,
        answers: {},
        startTime: performance.now(),
        submitted: false
      })
    } catch (error) {
      console.error('Errore quiz concetto:', error)
      setConceptError('Impossibile generare il quiz per il concetto selezionato.')
    }
  }

  const handleSubmitQuiz = async () => {
    if (!activeQuiz || !selectedCourse) return

    const { answers, quiz, concept, startTime } = activeQuiz
    const total = quiz.questions.length
    let correct = 0

    quiz.questions.forEach((question, index) => {
      if (answers[index] === question.correct) {
        correct += 1
      }
    })

    const timeSeconds = (performance.now() - startTime) / 1000
    const score = correct / total

    try {
      await fetch(`${API_BASE_URL}/courses/${selectedCourse}/concepts/${concept.id}/quiz-results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept_name: concept.name,
          chapter_title: concept.chapter?.title,
          score,
          time_seconds: timeSeconds,
          correct_answers: correct,
          total_questions: total
        })
      })

      await loadConceptMetrics(selectedCourse)
    } catch (error) {
      console.error('Errore salvataggio quiz concetto:', error)
    }

    setActiveQuiz({
      ...activeQuiz,
      submitted: true,
      result: { score, correct, total, timeSeconds }
    })
  }

  const renderConceptFocus = () => {
    if (!selectedCourse) return null

    const concepts = conceptMap?.concepts || []

    return (
      <div className="mb-6 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Target className="h-4 w-4 text-purple-600" />
            Concetti su cui concentrarsi
          </h2>
          <div className="flex items-center gap-2">
            {conceptsLoading ? (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <RefreshCw className="h-3 w-3 animate-spin" /> Caricamento…
              </span>
            ) : conceptMap ? (
              <span className="text-xs text-gray-500">
                {concepts.length} concetti disponibili
              </span>
            ) : null}
            <button
              onClick={handleGenerateConceptMap}
              disabled={conceptsGenerating}
              className="flex items-center gap-1 rounded-md border border-purple-200 px-3 py-1 text-xs font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-60"
            >
              {conceptsGenerating ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Filter className="h-3 w-3" />}
              Rigenera mappa
            </button>
          </div>
        </div>

        {conceptError && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            {conceptError}
          </div>
        )}
        {conceptsGenerating && (
          <div className="rounded-md border border-purple-100 bg-purple-50 p-3 text-xs text-purple-700">
            <p className="mb-2 flex items-center gap-2 font-medium">
              <RefreshCw className="h-3 w-3 animate-spin" />
              Generazione della mappa in corso…
            </p>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-purple-100">
              <div
                className="h-full rounded-full bg-purple-500 transition-all duration-300 ease-out"
                style={{ width: `${Math.min(conceptProgress, 100)}%` }}
              />
            </div>
            <p className="mt-2 text-[11px] text-purple-600">
              {conceptProgress >= 95
                ? 'Allineamento con il modello completato, in attesa della risposta…'
                : `Avanzamento stimato: ${Math.max(0, conceptProgress).toFixed(0)}%`}
            </p>
          </div>
        )}

        {concepts.length > 0 && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {concepts.map(concept => {
                const isSelected = selectedConceptIds.includes(concept.id)
                const metrics = conceptMetrics[concept.id]
                const difficultyBadge = metrics ? `${(metrics.stats.average_score * 100).toFixed(0)}%` : '—'

                return (
                  <button
                    key={concept.id}
                    onClick={() => toggleConcept(concept.id)}
                    className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                      isSelected
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                    }`}
                  >
                    <span className="font-medium">{concept.name}</span>
                    <span className="ml-2 text-[10px] text-gray-500">{difficultyBadge}</span>
                  </button>
                )
              })}
            </div>

            {selectedConcepts.length > 0 && (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                {selectedConcepts.map(concept => {
                  const metrics = conceptMetrics[concept.id]
                  return (
                    <div key={concept.id} className="mb-3 last:mb-0">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-gray-900">{concept.name}</h3>
                        <button
                          className="text-xs text-blue-600 hover:text-blue-700"
                          onClick={() => handleStartQuiz(concept)}
                        >
                          Genera quiz
                        </button>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">Capitolo: {concept.chapter?.title || 'N/A'}</p>
                      <p className="text-xs text-gray-600 mt-1">Obiettivi: {concept.learning_objectives.slice(0, 2).join('; ')}</p>
                      {metrics && (
                        <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-gray-500">
                          <span>Media quiz: {(metrics.stats.average_score * 100).toFixed(0)}%</span>
                          <span>Tentativi: {metrics.stats.attempts_count}</span>
                          <span>Tempo medio: {metrics.stats.average_time_seconds.toFixed(0)}s</span>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {!conceptsLoading && !conceptMap && !conceptError && (
          <button
            onClick={handleGenerateConceptMap}
            disabled={conceptsGenerating}
            className="flex items-center gap-2 rounded-md border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-600 hover:border-purple-300 hover:text-purple-700"
          >
            <Brain className="h-4 w-4" />
            Genera mappa concettuale del corso
          </button>
        )}
      </div>
    )
  }

  const renderQuizModal = () => {
    if (!activeQuiz) return null

    const { concept, quiz, answers, submitted, result } = activeQuiz

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
        <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Quiz: {concept.name}</h2>
              <p className="text-xs text-gray-500">{quiz.difficulty.toUpperCase()} • {quiz.questions.length} domande</p>
            </div>
            <button className="text-sm text-gray-500 hover:text-gray-700" onClick={() => setActiveQuiz(null)}>
              Chiudi
            </button>
          </div>

          <div className="space-y-6">
            {quiz.questions.map((question, index) => (
              <div key={index} className="rounded-lg border border-gray-200 p-4">
                <div className="mb-3 text-sm font-semibold text-gray-800">
                  {index + 1}. {question.question}
                </div>
                <div className="space-y-2">
                  {Object.entries(question.options).map(([key, value]) => {
                    const isSelected = answers[index] === key
                    const isCorrect = submitted && question.correct === key
                    const isWrongSelection = submitted && isSelected && question.correct !== key

                    return (
                      <label
                        key={key}
                        className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
                          isCorrect
                            ? 'border-green-400 bg-green-50 text-green-800'
                            : isWrongSelection
                            ? 'border-red-400 bg-red-50 text-red-800'
                            : isSelected
                            ? 'border-blue-400 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name={`question-${index}`}
                          value={key}
                          disabled={submitted}
                          checked={isSelected}
                          onChange={() =>
                            setActiveQuiz(prev => prev ? {
                              ...prev,
                              answers: { ...prev.answers, [index]: key }
                            } : prev)
                          }
                        />
                        <span className="font-medium">{key}.</span>
                        <span>{value}</span>
                      </label>
                    )
                  })}
                </div>
                {submitted && (
                  <p className="mt-2 text-xs text-gray-600">
                    Spiegazione: {question.explanation}
                  </p>
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between">
            {submitted && result ? (
              <div className="text-sm text-gray-700">
                Punteggio: <span className="font-semibold">{(result.score * 100).toFixed(0)}%</span> •
                Risposte corrette: {result.correct}/{result.total} • Tempo: {result.timeSeconds.toFixed(1)}s
              </div>
            ) : (
              <div className="text-xs text-gray-500">
                Seleziona una risposta per ogni domanda, poi invia il quiz.
              </div>
            )}
            <div className="flex items-center gap-3">
              {!submitted && (
                <button
                  onClick={handleSubmitQuiz}
                  disabled={Object.keys(answers).length !== quiz.questions.length}
                  className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-60"
                >
                  Invia risposte
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const handleClearConversation = () => {
    setMessages([])
    setActiveQuiz(null)
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    handleSendMessage()
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Chat Area */}
        <div className="lg:col-span-3 space-y-6">
          <div className="card">
        <div className="space-y-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <CourseSelector
              courses={courses}
              selectedCourse={selectedCourse}
              onCourseChange={setSelectedCourse}
            />
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <label className="inline-flex items-center gap-1">
                  <input
                    type="checkbox"
                    className="h-4 w-4"
                    checked={ragEnabled}
                    onChange={(e) => setRagEnabled(e.target.checked)}
                  />
                  RAG attivo
                </label>
                {llmStatus && (
                  <button
                    onClick={() => setShowLLMStatus(prev => !prev)}
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] ${
                      llmStatus.available
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-amber-50 text-amber-700'
                    }`}
                  >
                    {llmStatus.available ? <Zap className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
                    {llmStatus.available ? 'LLM disponibile' : 'LLM non disponibile'}
                  </button>
                )}
              </div>
              <BookSelector
                books={books}
                selectedBook={selectedBook}
                onBookChange={setSelectedBook}
                disabled={!selectedCourse}
              />
            </div>
          </div>

          {showLLMStatus && llmStatus && (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-xs text-gray-600">
              Provider corrente: <strong>{llmStatus.current}</strong> • Fallback: {llmStatus.fallbacks.join(', ') || 'Nessuno'} • Totale provider configurati: {llmStatus.totalProviders}
            </div>
          )}
        </div>
      </div>

          {/* Concept Focus - Ora nella sidebar */}
        </div>

        {/* Sidebar with Concept Map */}
        <div className="lg:col-span-1 space-y-6">
          <ConceptVisualMap
            conceptMap={conceptMap}
            conceptMetrics={conceptMetrics}
            conceptsLoading={conceptsLoading}
            conceptsGenerating={conceptsGenerating}
            onConceptToggle={toggleConcept}
            selectedConceptIds={selectedConceptIds}
            onConceptQuiz={handleStartQuiz}
            expandedByDefault={showConceptMap}
          />

          {/* Legacy concept focus info - ridotto */}
          {selectedConcepts.length > 0 && (
            <div className="bg-white border rounded-xl shadow-sm p-4">
              <h4 className="font-medium text-gray-900 mb-2 text-sm">Focus Attuale</h4>
              <div className="space-y-2">
                {selectedConcepts.map(concept => (
                  <div key={concept.id} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 truncate">{concept.name}</span>
                    <button
                      className="text-xs text-blue-600 hover:text-blue-700"
                      onClick={() => handleStartQuiz(concept)}
                    >
                      Quiz
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Back to main chat area */}
        <div className="lg:col-span-3 space-y-6">
          <div className="card min-h-[320px]">
        {messages.length === 0 && !isLoading ? (
          <div className="flex h-48 flex-col items-center justify-center text-center text-sm text-gray-500">
            <Brain className="mb-3 h-8 w-8 text-purple-500" />
            {selectedCourse && selectedCourseData ? (
                <div className="space-y-4">
                  <p>Inizia la tua sessione di studio! Ecco alcuni suggerimenti:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <button
                      onClick={() => setInput("Spiegami i concetti fondamentali di questo corso")}
                      className="px-3 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors text-xs"
                    >
                      📚 Concetti fondamentali
                    </button>
                    <button
                      onClick={() => setInput("Quali sono gli obiettivi principali di questo corso?")}
                      className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-xs"
                    >
                      🎯 Obiettivi del corso
                    </button>
                    <button
                      onClick={() => setInput("Dammi un esempio pratico di come applicare questi concetti")}
                      className="px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-xs"
                    >
                      💡 Esempi pratici
                    </button>
                    <button
                      onClick={() => setInput("Come posso prepararmi al meglio per gli esami?")}
                      className="px-3 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors text-xs"
                    >
                      📝 Preparazione esami
                    </button>
                    {selectedBook && selectedBookData && (
                      <button
                        onClick={() => setInput(`Analizziamo il libro "${selectedBookData.title}" e i suoi concetti principali`)}
                        className="px-3 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors text-xs"
                      >
                        📖 Analizza libro
                      </button>
                    )}
                    {selectedConcepts.length > 0 && (
                      <button
                        onClick={() => setInput(`Approfondiamo i concetti: ${selectedConcepts.map(c => c.name).join(', ')}`)}
                        className="px-3 py-2 bg-pink-100 text-pink-700 rounded-lg hover:bg-pink-200 transition-colors text-xs"
                      >
                        🧠 Approfondisci concetti
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-3">Oppure fai una domanda personalizzata...</p>
                </div>
              ) : (
                <p>Seleziona prima un corso per iniziare a chattare con il tutor AI.</p>
              )}
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map(message => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-start text-sm text-gray-500">
                <div className="flex items-center gap-2 rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Generazione risposta…
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex space-x-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={selectedCourse ? 'Fai la tua domanda...' : 'Seleziona prima un corso…'}
              disabled={!selectedCourse || isLoading}
              className="form-input flex-1"
            />
            <button
              type="submit"
              disabled={!input.trim() || !selectedCourse || isLoading}
              className="btn btn-primary flex items-center gap-2 disabled:opacity-60"
            >
              {isLoading ? <div className="loading-spinner"></div> : <Send className="h-4 w-4" />}
              Invia
            </button>
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <button
              type="button"
              onClick={handleClearConversation}
              className="text-gray-500 hover:text-gray-700"
            >
              Svuota conversazione
            </button>
            {selectedConcepts.length > 0 && (
              <span>Focus: {selectedConcepts.map(concept => concept.name).join(', ')}</span>
            )}
          </div>
        </form>
      </div>

      {renderQuizModal()}
        </div>
      </div>
    </div>
  )
}
