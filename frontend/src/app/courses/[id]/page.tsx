'use client'

import { useState, useEffect, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, FileText, MessageSquare, BarChart3, Trash2, BookOpen, Presentation, Calendar, Target, Merge, RefreshCw } from 'lucide-react'
import { StudyProgress } from '@/components/StudyProgress'
import BackgroundTaskProgress from '@/components/BackgroundTaskProgress'
import toast from 'react-hot-toast'
import BookCard from '@/components/BookCard'

interface Course {
  id: string
  name: string
  description: string
  subject: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
}

interface BookChapter {
  title: string
  summary: string
  estimated_minutes: number | null
  topics: string[]
}

interface Book {
  id: string
  title: string
  author: string
  description: string
  year: string
  publisher: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
  chapters: BookChapter[]
  tags: string[]
  materials?: Array<{
    filename: string
    size: number
  }>
}

interface ConceptMetricAttempt {
  timestamp: string
  score: number
  time_seconds: number
  correct_answers: number
  total_questions: number
}

interface ConceptMetricStats {
  average_score: number
  average_time_seconds: number
  attempts_count: number
  best_score: number
  latest_score: number
  latest_attempt_at: string | null
}

interface ConceptMetric {
  concept_name: string
  chapter_title: string | null
  attempts: ConceptMetricAttempt[]
  stats: ConceptMetricStats
}

const toStringValue = (value: unknown): string => {
  if (typeof value === 'string') {
    return value
  }
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
}

const toNumberValue = (value: unknown): number => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number.parseFloat(value)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }
  return 0
}

const toPositiveInteger = (value: unknown): number => {
  const numeric = toNumberValue(value)
  if (!Number.isFinite(numeric)) {
    return 0
  }
  return Math.max(0, Math.floor(numeric))
}

const normalizeAttempt = (attempt: unknown): ConceptMetricAttempt | null => {
  if (!attempt || typeof attempt !== 'object') {
    return null
  }
  const record = attempt as Record<string, unknown>
  const timestamp = toStringValue(record.timestamp)
  if (!timestamp) {
    return null
  }
  return {
    timestamp,
    score: toNumberValue(record.score),
    time_seconds: toNumberValue(record.time_seconds),
    correct_answers: Math.max(0, Math.floor(toNumberValue(record.correct_answers))),
    total_questions: Math.max(0, Math.floor(toNumberValue(record.total_questions)))
  }
}

const normalizeConceptMetric = (conceptId: string, metric: unknown): ({ id: string } & ConceptMetric) => {
  const record = metric && typeof metric === 'object' ? metric as Record<string, unknown> : {}
  const attemptsRaw = Array.isArray(record.attempts) ? record.attempts : []
  const attempts = attemptsRaw
    .map(normalizeAttempt)
    .filter((attempt): attempt is ConceptMetricAttempt => Boolean(attempt))

  const statsRaw = record.stats && typeof record.stats === 'object' ? record.stats as Record<string, unknown> : {}
  const stats: ConceptMetricStats = {
    average_score: toNumberValue(statsRaw.average_score),
    average_time_seconds: toNumberValue(statsRaw.average_time_seconds),
    attempts_count: Math.max(0, Math.floor(toNumberValue(statsRaw.attempts_count))),
    best_score: toNumberValue(statsRaw.best_score),
    latest_score: toNumberValue(statsRaw.latest_score),
    latest_attempt_at: (toStringValue(statsRaw.latest_attempt_at) || null)
  }

  const conceptName = toStringValue(record.concept_name)
  const chapterTitleValue = record.chapter_title !== undefined && record.chapter_title !== null
    ? toStringValue(record.chapter_title)
    : ''

  return {
    id: conceptId,
    concept_name: conceptName || `Concetto ${conceptId}`,
    chapter_title: chapterTitleValue || null,
    attempts,
    stats
  }
}

const normalizeChapter = (chapter: unknown): BookChapter | null => {
  if (typeof chapter === 'string') {
    const title = chapter.trim()
    if (!title) return null
    return {
      title,
      summary: '',
      estimated_minutes: null,
      topics: []
    }
  }

  if (chapter && typeof chapter === 'object') {
    const data = chapter as Record<string, unknown>
    const rawTitle = typeof data.title === 'string' ? data.title : typeof data.name === 'string' ? data.name : ''
    const title = rawTitle.trim()
    if (!title) return null

    let estimated: number | null = null
    if (typeof data.estimated_minutes === 'number') {
      estimated = data.estimated_minutes
    } else if (typeof data.estimated_minutes === 'string' && data.estimated_minutes.trim()) {
      const parsed = Number.parseInt(data.estimated_minutes, 10)
      estimated = Number.isFinite(parsed) && parsed >= 0 ? parsed : null
    }

    const topicsSource = Array.isArray(data.topics) ? data.topics : []
    const topics = topicsSource
      .map(topic => toStringValue(topic))
      .filter((topic): topic is string => Boolean(topic))

    return {
      title,
      summary: typeof data.summary === 'string' ? data.summary.trim() : '',
      estimated_minutes: estimated,
      topics
    }
  }

  return null
}

const normalizeBook = (book: unknown): Book => {
  const record = (book && typeof book === 'object') ? book as Record<string, unknown> : {}
  const chaptersArray = Array.isArray(record.chapters) ? record.chapters : []
  const normalizedChapters = chaptersArray
    .map(normalizeChapter)
    .filter((chapter): chapter is BookChapter => Boolean(chapter))

  return {
    id: toStringValue(record.id),
    title: toStringValue(record.title),
    author: toStringValue(record.author),
    description: toStringValue(record.description),
    year: toStringValue(record.year),
    publisher: toStringValue(record.publisher),
    materials_count: toPositiveInteger(record.materials_count),
    study_sessions: toPositiveInteger(record.study_sessions),
    total_study_time: toPositiveInteger(record.total_study_time),
    created_at: toStringValue(record.created_at),
    chapters: normalizedChapters,
    tags: Array.isArray(record.tags) ? record.tags.map(tag => toStringValue(tag)).filter(Boolean) : []
  }
}

export default function CourseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'books' | 'progress' | 'quiz' | 'slides' | 'plans' | 'chat' | 'practice'>('books')
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [taskPreferences, setTaskPreferences] = useState({
    title: 'Piano di Studio Personalizzato',
    sessions_per_week: 3,
    session_duration: 45,
    difficulty_level: 'intermediate',
    difficulty_progression: 'graduale'
  })
  const [conceptMetrics, setConceptMetrics] = useState<Array<{ id: string } & ConceptMetric>>([])
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [metricsError, setMetricsError] = useState('')

  // Merge PDF states
  const [isMergingCourse, setIsMergingCourse] = useState(false)
  const [isMergingBook, setIsMergingBook] = useState<string | null>(null)
  const [mergeResult, setMergeResult] = useState<any>(null)

  useEffect(() => {
    fetchCourse()
    fetchBooks()
    fetchConceptMetrics()
  }, [courseId])

  const fetchCourse = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`)
      const data = await response.json()

      if (response.ok) {
        setCourse(data.course)
      } else {
        if (response.status === 404) {
          setError('Corso non trovato')
        } else {
          setError('Errore nel caricamento del corso')
        }
      }
    } catch (error) {
      console.error('Errore nel caricamento del corso:', error)
      setError('Errore di connessione al server')
    }
  }

  const fetchBooks = async () => {
    try {
      // Fetch course data which contains books directly
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        const courseData = data.course
        const books = courseData.books || []
        setBooks(books)
      } else {
        console.error('Errore nel caricamento dei libri')
      }
    } catch (error) {
      console.error('Errore nel caricamento dei libri:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchConceptMetrics = async () => {
    setMetricsLoading(true)
    setMetricsError('')
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/concepts/metrics`)
      if (response.ok) {
        const data = await response.json()
        const metricsMap = data.metrics ?? {}
        const normalized = Object.entries(metricsMap).map(([conceptId, rawMetric]) => normalizeConceptMetric(conceptId, rawMetric))
        setConceptMetrics(normalized)
      } else {
        setMetricsError('Errore nel caricamento delle metriche dei concetti')
      }
    } catch (err) {
      console.error('Errore nel caricamento delle metriche dei concetti:', err)
      setMetricsError('Errore di connessione nel recupero delle metriche')
    } finally {
      setMetricsLoading(false)
    }
  }

  const mergeBookPDFs = async (bookId: string) => {
    setIsMergingBook(bookId)
    setMergeResult(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/books/${bookId}/merge-pdf`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()
      setMergeResult(result)
    } catch (error) {
      console.error('Error merging book PDFs:', error)
      toast.error(`Errore nell'unione dei PDF: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`)
    } finally {
      setIsMergingBook(null)
    }
  }

  const mergeCoursePDFs = async () => {
    setIsMergingCourse(true)
    setMergeResult(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/merge-pdf`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()
      setMergeResult(result)
    } catch (error) {
      console.error('Error merging course PDFs:', error)
      toast.error(`Errore nell'unione dei PDF del corso: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`)
    } finally {
      setIsMergingCourse(false)
    }
  }

  const conceptSummary = useMemo(() => {
    const totalConcepts = conceptMetrics.length
    const totalAttempts = conceptMetrics.reduce((acc, metric) => acc + metric.stats.attempts_count, 0)
    const weightedScoreSum = conceptMetrics.reduce((acc, metric) => acc + (metric.stats.average_score * metric.stats.attempts_count), 0)
    const weightedTimeSum = conceptMetrics.reduce((acc, metric) => acc + (metric.stats.average_time_seconds * metric.stats.attempts_count), 0)
    const averageScore = totalAttempts > 0 ? weightedScoreSum / totalAttempts : 0
    const averageTime = totalAttempts > 0 ? weightedTimeSum / totalAttempts : 0
    const bestScore = conceptMetrics.reduce((best, metric) => Math.max(best, metric.stats.best_score), 0)
    const latestAttemptTimestamp = conceptMetrics.reduce((latest, metric) => {
      const latestTs = metric.stats.latest_attempt_at
      if (!latestTs) {
        return latest
      }
      const parsed = Date.parse(latestTs)
      if (Number.isNaN(parsed)) return latest
      return parsed > latest ? parsed : latest
    }, 0)

    return {
      totalConcepts,
      totalAttempts,
      averageScore,
      bestScore,
      averageTime,
      latestAttempt: latestAttemptTimestamp ? new Date(latestAttemptTimestamp) : null
    }
  }, [conceptMetrics])

  const handleDeleteCourse = async () => {
    if (!confirm(`Sei sicuro di voler eliminare il corso "${course?.name}"? Questa azione non può essere annullata.`)) {
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        toast.success('Corso eliminato')
        router.push('/')
      } else {
        toast.error('Errore nell\'eliminazione del corso')
      }
    } catch (error) {
      console.error('Errore nell\'eliminazione del corso:', error)
      toast.error('Errore nell\'eliminazione del corso')
    }
  }

  const createBackgroundStudyPlan = async () => {
    if (!courseId) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/study-plans/background`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_id: courseId,
          ...taskPreferences
        })
      })

      if (response.ok) {
        const data = await response.json()
        setCurrentTaskId(data.task_id)
        setShowTaskForm(false)
        setActiveTab('plans')
        toast.success('Piano di studio avviato')
      } else {
        toast.error('Errore nella creazione del piano di studio')
      }
    } catch (error) {
      console.error('Errore nella creazione del piano di studio:', error)
      toast.error('Errore nella creazione del piano di studio')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen" role="status" aria-busy="true" aria-live="polite">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600">
          <span className="sr-only">Caricamento corso…</span>
        </div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {error || 'Corso non trovato'}
        </h2>
        <Link href="/" className="btn btn-primary">
          Torna alla Home
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Link
            href="/"
            className="inline-flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna alla Home
          </Link>

          <button
            onClick={handleDeleteCourse}
            className="text-red-600 hover:text-red-800 flex items-center space-x-2"
          >
            <Trash2 className="h-4 w-4" />
            <span>Elimina Corso</span>
          </button>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{course.name}</h1>
              <p className="text-lg text-gray-600 mb-4">{course.subject}</p>
              <p className="text-gray-700 mb-6">{course.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <BookOpen className="h-6 w-6 text-blue-600 mb-2" />
                  <div className="text-2xl font-bold text-blue-900">{books.length}</div>
                  <div className="text-sm text-blue-700">Libri</div>
                </div>

                <div className="bg-green-50 rounded-lg p-4">
                  <FileText className="h-6 w-6 text-green-600 mb-2" />
                  <div className="text-2xl font-bold text-green-900">
                    {books.reduce((sum, book) => sum + book.materials_count, 0)}
                  </div>
                  <div className="text-sm text-green-700">Materiali totali</div>
                </div>

                <div className="bg-purple-50 rounded-lg p-4">
                  <MessageSquare className="h-6 w-6 text-purple-600 mb-2" />
                  <div className="text-2xl font-bold text-purple-900">{course.study_sessions}</div>
                  <div className="text-sm text-purple-700">Sessioni di studio</div>
                </div>

                <div className="bg-orange-50 rounded-lg p-4">
                  <BarChart3 className="h-6 w-6 text-orange-600 mb-2" />
                  <div className="text-2xl font-bold text-orange-900">
                    {Math.floor(course.total_study_time / 60)}h {course.total_study_time % 60}m
                  </div>
                  <div className="text-sm text-orange-700">Tempo totale di studio</div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 mt-6 pt-6 border-t border-gray-200">
            <Link
              href={`/courses/${course.id}/books`}
              className="btn btn-primary flex items-center space-x-2"
            >
              <BookOpen className="h-4 w-4" />
              <span>Gestisci Libri</span>
            </Link>

            {/* Study Button - links to first available book */}
            {books.length > 0 && (
              <Link
                href={`/courses/${course.id}/study?book=${books[0].id}&pdf=${books[0].materials?.[0] || 'default.pdf'}`}
                className="btn btn-primary flex items-center space-x-2 bg-green-600 hover:bg-green-700"
              >
                <BookOpen className="h-4 w-4" />
                <span>Study</span>
              </Link>
            )}

            <Link
              href={`/courses/${course.id}/chat`}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat con Tutor</span>
            </Link>

            <Link
              href={`/courses/${course.id}/practice`}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <Target className="h-4 w-4" />
              <span>Practice SRS</span>
            </Link>

            <Link
              href={`/courses/${course.id}/quiz`}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <BarChart3 className="h-4 w-4" />
              <span>Crea Quiz</span>
            </Link>

            {/* Course Merge PDF Button */}
            {books.reduce((sum, book) => sum + book.materials_count, 0) > 0 && (
              <button
                onClick={mergeCoursePDFs}
                disabled={isMergingCourse}
                className="btn btn-secondary flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isMergingCourse ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Unione in corso...</span>
                  </>
                ) : (
                  <>
                    <Merge className="h-4 w-4" />
                    <span>Unisci Tutti i PDF del Corso</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs" role="tablist">
            <button
              onClick={() => setActiveTab('books')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'books'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'books'}
            >
              Libri del Corso
            </button>

            <button
              onClick={() => setActiveTab('progress')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'progress'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'progress'}
            >
              Progressi di Studio
            </button>

            <button
              onClick={() => setActiveTab('quiz')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'quiz'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'quiz'}
            >
              Quiz e Test
            </button>

            <button
              onClick={() => setActiveTab('slides')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'slides'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'slides'}
            >
              Generatore Slide
            </button>

            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'chat'}
            >
              Chat Tutor AI
            </button>

            <button
              onClick={() => setActiveTab('practice')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'practice'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'practice'}
            >
              Practice SRS
            </button>

            <button
              onClick={() => setActiveTab('plans')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'plans'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              role="tab"
              aria-selected={activeTab === 'plans'}
            >
              Piani di Studio
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'books' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Libri del Corso</h3>
                  <p className="text-sm text-gray-600">Gestisci i libri e i materiali specifici per questo corso</p>
                </div>
                <Link
                  href={`/courses/${courseId}/books`}
                  className="btn btn-primary flex items-center space-x-2"
                >
                  <BookOpen className="h-4 w-4" />
                  <span>Gestisci Libri</span>
                </Link>
              </div>

              {books.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BookOpen className="h-10 w-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun libro ancora aggiunto</h3>
                  <p className="text-gray-600 mb-6">
                    Inizia aggiungendo il primo libro per questo corso
                  </p>
                  <Link
                    href={`/courses/${courseId}/books`}
                    className="btn btn-primary"
                  >
                    Aggiungi Libro
                  </Link>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Books Grid with BookCard Components */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {books.map((book) => (
                      <BookCard
                        key={book.id}
                        book={book}
                        courseId={courseId}
                      />
                    ))}
                  </div>

                  {/* PDF Merge Section - Maintained for legacy functionality */}
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Unione PDF</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Unisci tutti i PDF di un libro in un unico documento per una consultazione più facile.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {books.filter(book => book.materials_count > 0).map((book) => (
                        <div key={book.id} className="flex items-center justify-between p-3 bg-white rounded border border-gray-200">
                          <div className="flex-1">
                            <h4 className="text-sm font-medium text-gray-900 truncate">{book.title}</h4>
                            <p className="text-xs text-gray-500">{book.materials_count} file</p>
                          </div>
                          <button
                            onClick={() => mergeBookPDFs(book.id)}
                            disabled={isMergingBook === book.id}
                            className="btn btn-secondary text-sm bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed px-3 py-2 ml-2"
                            title="Unisci tutti i PDF di questo libro"
                          >
                            {isMergingBook === book.id ? (
                              <RefreshCw className="h-4 w-4 animate-spin" />
                            ) : (
                              <Merge className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Merge PDF Success Display */}
              {mergeResult && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-green-800">✅ PDF Unito con Successo</h3>
                      <p className="text-green-700 mb-2">
                        {mergeResult.merged_pdf?.total_files || mergeResult.merged_pdf?.files_merged?.length} PDF uniti in: {mergeResult.merged_pdf?.filename}
                      </p>
                      <p className="text-sm text-green-600">
                        Dimensione: {((mergeResult.merged_pdf?.size || 0) / (1024 * 1024)).toFixed(2)} MB
                      </p>

                      {/* Course merge details */}
                      {mergeResult.merged_pdf?.books_summary && (
                        <div className="mt-3">
                          <p className="text-sm text-green-600 mb-2">
                            {mergeResult.merged_pdf.total_books} libri processati:
                          </p>
                          <details className="text-xs text-green-600">
                            <summary className="cursor-pointer">Dettagli libri</summary>
                            <ul className="mt-1 ml-4">
                              {mergeResult.merged_pdf.books_summary.map((book: any, index: number) => (
                                <li key={index} className="mb-1">
                                  <strong>{book.book_title}:</strong> {book.files_count} file
                                </li>
                              ))}
                            </ul>
                          </details>
                        </div>
                      )}

                      {/* Book merge details */}
                      {mergeResult.merged_pdf?.files_merged && !mergeResult.merged_pdf?.books_summary && (
                        <details className="mt-2">
                          <summary className="text-sm text-green-600 cursor-pointer">File uniti</summary>
                          <ul className="text-xs text-green-600 mt-1 ml-4">
                            {mergeResult.merged_pdf.files_merged.map((filename: string, index: number) => (
                              <li key={index}>• {filename}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                    <button
                      onClick={() => setMergeResult(null)}
                      className="text-green-500 hover:text-green-700"
                    >
                      ×
                    </button>
                  </div>
                </div>
              )}

              {/* Stats */}
              {books.length > 0 && (
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistiche Libri</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Totale Libri</p>
                      <p className="text-2xl font-bold text-gray-900">{books.length}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Materiali Caricati</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {books.reduce((sum, book) => sum + book.materials_count, 0)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Sessioni di Studio</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {books.reduce((sum, book) => sum + book.study_sessions, 0)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Tempo Totale</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {Math.round(books.reduce((sum, book) => sum + book.total_study_time, 0) / 60)}h
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Capitoli totali</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {books.reduce((sum, book) => sum + book.chapters.length, 0)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Minuti suggeriti</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {books.reduce((sum, book) => sum + book.chapters.reduce((acc, chapter) => acc + (chapter.estimated_minutes || 0), 0), 0)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'progress' && (
            <StudyProgress courseId={courseId} />
          )}

          {activeTab === 'quiz' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Quiz e Valutazioni</h3>
                  <p className="text-sm text-gray-600">
                    Monitora le performance sui concetti chiave e crea nuovi quiz di verifica
                  </p>
                </div>
                <Link
                  href={`/courses/${course.id}/quiz`}
                  className="btn btn-primary flex items-center space-x-2"
                >
                  <BarChart3 className="h-4 w-4" />
                  <span>Crea Nuovo Quiz</span>
                </Link>
              </div>

              {metricsLoading ? (
                <div className="flex justify-center items-center py-12">
                  <div className="text-center">
                    <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
                    <p className="mt-3 text-gray-600 text-sm">Caricamento metriche dei quiz...</p>
                  </div>
                </div>
              ) : metricsError ? (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {metricsError}
                </div>
              ) : conceptMetrics.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BarChart3 className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun quiz registrato</h3>
                  <p className="text-gray-600 mb-4">
                    Genera un quiz sui concetti del corso per iniziare a tracciare i progressi.
                  </p>
                  <Link href={`/courses/${course.id}/quiz`} className="btn btn-primary">
                    Crea un Quiz
                  </Link>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-700">Concetti monitorati</p>
                      <p className="text-2xl font-bold text-blue-900">{conceptSummary.totalConcepts}</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <p className="text-sm text-purple-700">Quiz svolti</p>
                      <p className="text-2xl font-bold text-purple-900">{conceptSummary.totalAttempts}</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="text-sm text-green-700">Score medio</p>
                      <p className="text-2xl font-bold text-green-900">{Math.round(conceptSummary.averageScore * 100)}%</p>
                    </div>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                      <p className="text-sm text-amber-700">Tempo medio</p>
                      <p className="text-2xl font-bold text-amber-900">{Math.round(conceptSummary.averageTime)}s</p>
                    </div>
                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                      <p className="text-sm text-indigo-700">Miglior punteggio</p>
                      <p className="text-2xl font-bold text-indigo-900">{Math.round(conceptSummary.bestScore * 100)}%</p>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-700">Ultimo tentativo</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {conceptSummary.latestAttempt
                          ? conceptSummary.latestAttempt.toLocaleDateString() + ' ' + conceptSummary.latestAttempt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                          : '—'}
                      </p>
                    </div>
                  </div>

                  <div className="overflow-x-auto border border-gray-200 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Concetto</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Capitolo</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Tentativi</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Media</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ultimo</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Migliore</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ultimo tentativo</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {conceptMetrics.map((metric) => {
                          const latestAttempt = metric.stats.latest_attempt_at ? new Date(metric.stats.latest_attempt_at) : null
                          return (
                            <tr key={metric.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm text-gray-900">
                                <p className="font-medium text-gray-800">{metric.concept_name}</p>
                                {metric.attempts.length > 0 && (
                                  <p className="text-xs text-gray-500">
                                    Ultimo punteggio registrato: {Math.round(metric.stats.latest_score * 100)}%
                                  </p>
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">
                                {metric.chapter_title || '—'}
                              </td>
                              <td className="px-4 py-3 text-center text-sm text-gray-600">
                                {metric.stats.attempts_count}
                              </td>
                              <td className="px-4 py-3 text-center text-sm text-gray-600">
                                {Math.round(metric.stats.average_score * 100)}%
                              </td>
                              <td className="px-4 py-3 text-center text-sm text-gray-600">
                                {Math.round(metric.stats.latest_score * 100)}%
                              </td>
                              <td className="px-4 py-3 text-center text-sm text-gray-600">
                                {Math.round(metric.stats.best_score * 100)}%
                              </td>
                              <td className="px-4 py-3 text-center text-sm text-gray-600">
                                {latestAttempt ? latestAttempt.toLocaleString() : '—'}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'slides' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Generatore di Slide AI</h3>
                  <p className="text-sm text-gray-600">Crea presentazioni professionali basate sui materiali del corso</p>
                </div>
                <Link
                  href={`/courses/${courseId}/slides`}
                  className="btn btn-primary flex items-center space-x-2"
                >
                  <Presentation className="h-4 w-4" />
                  <span>Crea Slide</span>
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="text-purple-600 mb-2">🎨</div>
                  <h4 className="font-medium text-purple-900 mb-1">Temi Personalizzabili</h4>
                  <p className="text-sm text-purple-700">Scegli tra diversi temi per adattare lo stile alle tue esigenze</p>
                </div>
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-blue-600 mb-2">🤖</div>
                  <h4 className="font-medium text-blue-900 mb-1">AI-Powered</h4>
                  <p className="text-sm text-blue-700">Generazione automatica basata sui tuoi materiali di studio</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="text-green-600 mb-2">📝</div>
                  <h4 className="font-medium text-green-900 mb-1">Modifica Facile</h4>
                  <p className="text-sm text-green-700">Modifica e personalizza ogni slide secondo le tue necessità</p>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="text-orange-600 mb-2">🚀</div>
                  <h4 className="font-medium text-orange-900 mb-1">Export Veloce</h4>
                  <p className="text-sm text-orange-700">Esporta le presentazioni in vari formati</p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <div className="text-red-600 mb-2">📊</div>
                  <h4 className="font-medium text-red-900 mb-1">Layout Multipli</h4>
                  <p className="text-sm text-red-700">Scegli tra diversi layout per ogni tipo di contenuto</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="text-gray-600 mb-2">💡</div>
                  <h4 className="font-medium text-gray-900 mb-1">Intelligente</h4>
                  <p className="text-sm text-gray-700">L'AI analizza i contenuti per creare slide pertinenti</p>
                </div>
              </div>

              {books.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Presentation className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun materiale disponibile</h3>
                  <p className="text-gray-600 mb-4">
                    Aggiungi libri e materiali al corso per generare slide basate sui contenuti
                  </p>
                  <Link
                    href={`/courses/${courseId}/books`}
                    className="btn btn-primary"
                  >
                    Aggiungi Materiali
                  </Link>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-4">
                    Hai <span className="font-semibold">{books.length}</span> libri disponibili per generare slide
                  </p>
                  <Link
                    href={`/courses/${courseId}/slides`}
                    className="btn btn-primary"
                  >
                    <Presentation className="h-4 w-4 mr-2" />
                    Inizia a Creare Slide
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Study Plans Tab */}
          {activeTab === 'chat' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Chat Tutor AI</h3>
                  <p className="text-sm text-gray-600">
                    Conversa con il tutor AI specializzato per questo corso
                  </p>
                </div>
                <Link
                  href={`/courses/${courseId}/chat`}
                  className="btn btn-primary flex items-center space-x-2"
                >
                  <MessageSquare className="h-4 w-4" />
                  <span>Apri Chat Completa</span>
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-blue-600 mb-2">🧠</div>
                  <h4 className="font-medium text-blue-900 mb-1">Contesto Intelligente</h4>
                  <p className="text-sm text-blue-700">Il tutor ricorda le conversazioni precedenti e adatta le risposte</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="text-green-600 mb-2">📚</div>
                  <h4 className="font-medium text-green-900 mb-1">Basato sui Materiali</h4>
                  <p className="text-sm text-green-700">Risposte basate sui libri e materiali del corso</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="text-purple-600 mb-2">🎯</div>
                  <h4 className="font-medium text-purple-900 mb-1">Personalizzato</h4>
                  <p className="text-sm text-purple-700">Apprende il tuo stile e il tuo livello di conoscenza</p>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="text-orange-600 mb-2">💬</div>
                  <h4 className="font-medium text-orange-900 mb-1">Sessioni Persistenti</h4>
                  <p className="text-sm text-orange-700">Le conversazioni vengono salvate e possono essere continuate</p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <div className="text-red-600 mb-2">📊</div>
                  <h4 className="font-medium text-red-900 mb-1">Analisi di Apprendimento</h4>
                  <p className="text-sm text-red-700">Traccia i progressi e i concetti discussi</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="text-gray-600 mb-2">🔍</div>
                  <h4 className="font-medium text-gray-900 mb-1">Ricerca Avanzata</h4>
                  <p className="text-sm text-gray-700">Trova informazioni velocemente tra tutti i materiali</p>
                </div>
              </div>

              {books.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageSquare className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun materiale per la chat</h3>
                  <p className="text-gray-600 mb-4">
                    Aggiungi libri e materiali al corso per iniziare a chattare con il tutor AI
                  </p>
                  <Link
                    href={`/courses/${courseId}/books`}
                    className="btn btn-primary"
                  >
                    Aggiungi Materiali
                  </Link>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-4">
                    Hai <span className="font-semibold">{books.length}</span> libri disponibili per la chat
                  </p>
                  <Link
                    href={`/courses/${courseId}/chat`}
                    className="btn btn-primary"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Inizia a Chattare
                  </Link>
                </div>
              )}
            </div>
          )}

          {activeTab === 'practice' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Practice SRS</h3>
                  <p className="text-sm text-gray-600">
                    Sistema di ripetizione spaziata per massimizzare la ritenzione a lungo termine
                  </p>
                </div>
                <Link
                  href={`/courses/${courseId}/practice`}
                  className="btn btn-primary flex items-center space-x-2"
                >
                  <Target className="h-4 w-4" />
                  <span>Inizia Practice</span>
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-blue-600 mb-2">🧠</div>
                  <h4 className="font-medium text-blue-900 mb-1">SM-2 Algorithm</h4>
                  <p className="text-sm text-blue-700">Algoritmo scientificamente provato per scheduling ottimale</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="text-green-600 mb-2">📈</div>
                  <h4 className="font-medium text-green-900 mb-1">Adattivo</h4>
                  <p className="text-sm text-green-700">Si adatta al tuo ritmo e performance</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="text-purple-600 mb-2">🎯</div>
                  <h4 className="font-medium text-purple-900 mb-1">Intelligente</h4>
                  <p className="text-sm text-purple-700">Genera schede automaticamente dalle conversazioni</p>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="text-orange-600 mb-2">⚡</div>
                  <h4 className="font-medium text-orange-900 mb-1">Efficiente</h4>
                  <p className="text-sm text-orange-700">Studia solo quando serve, ottimizzando il tempo</p>
                </div>
              </div>

              <div className="bg-amber-50 rounded-lg border border-amber-200 p-6">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                      <Target className="h-5 w-5 text-amber-600" />
                    </div>
                  </div>
                  <div>
                    <h4 className="text-lg font-medium text-amber-900 mb-2">Come funziona il Practice SRS?</h4>
                    <div className="text-sm text-amber-800 space-y-2">
                      <p>• Le schede vengono presentate quando è il momento ottimale per ripassare</p>
                      <p>• Valuta la tua qualità di risposta con un click (0-5)</p>
                      <p>• L'algoritmo calcola automaticamente quando ripresentare la scheda</p>
                      <p>• Le schede difficili vengono ripetite più spesso, quelle facili meno spesso</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        {activeTab === 'plans' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Piani di Studio</h3>
                  <p className="text-sm text-gray-600">Genera piani di studio personalizzati basati sui materiali del corso</p>
                </div>
                <button
                  onClick={() => setShowTaskForm(true)}
                  className="btn btn-primary flex items-center space-x-2"
                >
                  <Calendar className="h-4 w-4" />
                  <span>Crea Piano di Studio</span>
                </button>
              </div>

              {/* Task Creation Form Modal */}
              {showTaskForm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 w-full max-w-md">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Crea Piano di Studio</h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Titolo</label>
                        <input
                          type="text"
                          value={taskPreferences.title}
                          onChange={(e) => setTaskPreferences({...taskPreferences, title: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Sessioni/Settimana</label>
                          <select
                            value={taskPreferences.sessions_per_week}
                            onChange={(e) => setTaskPreferences({...taskPreferences, sessions_per_week: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value={1}>1</option>
                            <option value={2}>2</option>
                            <option value={3}>3</option>
                            <option value={4}>4</option>
                            <option value={5}>5</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Durata (minuti)</label>
                          <select
                            value={taskPreferences.session_duration}
                            onChange={(e) => setTaskPreferences({...taskPreferences, session_duration: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value={30}>30</option>
                            <option value={45}>45</option>
                            <option value={60}>60</option>
                            <option value={90}>90</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Livello Difficoltà</label>
                        <select
                          value={taskPreferences.difficulty_level}
                          onChange={(e) => setTaskPreferences({...taskPreferences, difficulty_level: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="principiante">Principiante</option>
                          <option value="intermediate">Intermedio</option>
                          <option value="avanzato">Avanzato</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Progressione Difficoltà</label>
                        <select
                          value={taskPreferences.difficulty_progression}
                          onChange={(e) => setTaskPreferences({...taskPreferences, difficulty_progression: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="graduale">Graduale</option>
                          <option value="costante">Costante</option>
                          <option value="flessibile">Flessibile</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex justify-end space-x-3 mt-6">
                      <button
                        onClick={() => setShowTaskForm(false)}
                        className="px-4 py-2 text-gray-600 hover:text-gray-800"
                      >
                        Annulla
                      </button>
                      <button
                        onClick={createBackgroundStudyPlan}
                        className="btn btn-primary"
                      >
                        Crea Piano
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Task Progress */}
              {currentTaskId && (
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Stato Generazione</h4>
                  <BackgroundTaskProgress
                    taskId={currentTaskId}
                    onComplete={(result) => {
                      console.log('Study plan completed:', result)
                      // Potrebbe reindirizzare alla pagina dei piani di studio
                      setCurrentTaskId(null)
                    }}
                    onError={(error) => {
                      console.error('Study plan failed:', error)
                      setCurrentTaskId(null)
                    }}
                    onCancel={() => {
                      setCurrentTaskId(null)
                    }}
                  />
                </div>
              )}

              {/* Study Plans List */}
              {!currentTaskId && !showTaskForm && (
                <div className="text-center py-12">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Calendar className="h-10 w-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun piano di studio ancora creato</h3>
                  <p className="text-gray-600 mb-6">
                    Crea il tuo primo piano di studio personalizzato per iniziare
                  </p>
                  <button
                    onClick={() => setShowTaskForm(true)}
                    className="btn btn-primary"
                  >
                    <Calendar className="h-4 w-4 mr-2" />
                    Crea il Tuo Piano
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
