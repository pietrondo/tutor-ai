'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Brain, RefreshCw, Loader2, Save, BookOpen, Sparkles, FileText, Lightbulb } from 'lucide-react'
import toast from 'react-hot-toast'
import { MindmapExplorer } from '@/components/MindmapExplorer'
import { StudyMindmap, StudyMindmapNode, ExpandedStudyNode, StudySessionContext } from '@/types/mindmap'
import VisualMindmap, { type MindmapData } from '@/components/VisualMindmap'
import { mindmapService, type MindmapStorage, type MindmapStoragePayload } from '@/services/mindmapService'
import { fetchFromBackend } from '@/lib/api'


interface ParsedResponse<T> {
  payload: T | null
  rawText: string
}

const parseJsonSafely = async <T,>(response: Response): Promise<ParsedResponse<T>> => {
  const rawText = await response.text()
  if (!rawText) {
    return { payload: null, rawText: '' }
  }

  try {
    return { payload: JSON.parse(rawText) as T, rawText: '' }
  } catch (error) {
    console.error('Failed to parse response as JSON:', error, rawText)
    return { payload: null, rawText }
  }
}

interface Book {
  id: string
  title: string
  author: string
  materials: Array<{
    filename: string
    file_path: string
  }>
}

type MindmapSource =
  | string
  | {
      source?: string
      chunk_index?: number
      relevance_score?: number
      [key: string]: unknown
    }

interface MindmapGenerationResponse {
  success: boolean
  mindmap?: StudyMindmap
  markdown?: string
  references?: string[]
  sources?: MindmapSource[]
  enhanced?: boolean
  session_aware?: boolean
}

interface MindmapExpandApiResponse {
  success: boolean
  expanded_nodes?: ExpandedStudyNode[]
  sources_used?: string[]
}

interface MindmapEditApiResponse {
  success: boolean
  edited_node?: ExpandedStudyNode
  sources_used?: string[]
}

type MindmapSaveInput = MindmapStoragePayload | MindmapData

const isStoragePayload = (value: MindmapSaveInput): value is MindmapStoragePayload =>
  typeof value === 'object' &&
  value !== null &&
  ('structured_map' in value || 'content_markdown' in value)

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []

const toMindmapSources = (value: unknown): MindmapSource[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is MindmapSource => typeof item === 'string' || isObject(item))
}

const hasMindmapNodes = (value: unknown): value is StudyMindmap => {
  if (!isObject(value)) return false
  const candidate = value as Partial<StudyMindmap>
  return Array.isArray(candidate.nodes)
}

const isMindmapGenerationResponse = (value: unknown): value is MindmapGenerationResponse => {
  if (!isObject(value)) return false
  return typeof value.success === 'boolean'
}

const isExpandedStudyNode = (value: unknown): value is ExpandedStudyNode => {
  if (!isObject(value)) return false
  return typeof value.title === 'string' && typeof value.id === 'string'
}

const collectSessionContext = async (courseId: string, bookId: string): Promise<StudySessionContext | null> => {
  // Collect current study session context for enhanced mindmap generation
  try {
    // Get current progress data
    const progressResponse = await fetchFromBackend(`/courses/${courseId}/progress`)
    const progressData = progressResponse.ok ? await progressResponse.json() : null

    // Get recent study sessions
    const sessionsResponse = await fetchFromBackend(`/courses/${courseId}/study-sessions?limit=10`)
    const sessionsData = sessionsResponse.ok ? await sessionsResponse.json() : { sessions: [] }

    // Get quiz performance if available
    const quizResponse = await fetchFromBackend(`/courses/${courseId}/quiz/performance`)
    const quizData = quizResponse.ok ? await quizResponse.json() : { performance: {} }

    // Get today's study time
    const todayResponse = await fetchFromBackend(`/courses/${courseId}/study-time/today`)
    const todayData = todayResponse.ok ? await todayResponse.json() : { minutes: 0 }

    // Extract relevant data
    const recentSessions = sessionsData.sessions || []
    const recentlyStudied = recentSessions
      .slice(-5)
      .flatMap((session: any) => session.topics_studied || [])
      .filter(Boolean)

    const weakAreas = progressData?.weak_areas || []
    const masteryLevels = progressData?.mastery_levels || {}
    const quizPerformance = quizData.performance || {}

    // Build session context
    const sessionContext: StudySessionContext = {
      session_id: `session_${Date.now()}`,
      course_id: courseId,
      book_id: bookId,
      current_progress: progressData?.progress_percentage || 0,
      weak_areas: weakAreas,
      mastery_levels: masteryLevels,
      quiz_performance: quizPerformance,
      study_time_today: todayData.minutes || 0,
      preferred_difficulty: 'adaptive',
      recently_studied: recentlyStudied,
      goals: progressData?.current_goals || []
    }

    console.log('🧠 Collected session context:', sessionContext)
    return sessionContext

  } catch (error) {
    console.warn('⚠️ Could not collect session context, using standard generation:', error)
    return null
  }
}

const isMindmapExpandResponse = (value: unknown): value is MindmapExpandApiResponse => {
  if (!isObject(value) || typeof value.success !== 'boolean') {
    return false
  }
  if (value.expanded_nodes && !Array.isArray(value.expanded_nodes)) {
    return false
  }
  if (Array.isArray(value.expanded_nodes) && !value.expanded_nodes.every(isExpandedStudyNode)) {
    return false
  }
  if (value.sources_used && !Array.isArray(value.sources_used)) {
    return false
  }
  return true
}

interface MindmapClientProps {
  courseId: string
  bookId: string
}

export default function MindmapClient({ courseId, bookId }: MindmapClientProps) {
  const params = useParams()
  const router = useRouter()
  const courseParam = (params.id ?? params.courseId) as string | undefined
  const bookParam = params.bookId as string | undefined

  const effectiveCourseId = courseId || courseParam
  const effectiveBookId = bookId || bookParam

  const [book, setBook] = useState<Book | null>(null)
  const [courseName, setCourseName] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [mindmap, setMindmap] = useState<StudyMindmap | null>(null)
  const [markdown, setMarkdown] = useState<string>('')
  const [references, setReferences] = useState<string[]>([])
  const [sources, setSources] = useState<MindmapSource[]>([])
  const [saving, setSaving] = useState(false)
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null)
  const [error, setError] = useState('')

  const loadBookInfo = async () => {
    try {
      setLoading(true)
      const response = await fetchFromBackend(`/courses/${effectiveCourseId}/books/${effectiveBookId}`)
      if (!response.ok) {
        throw new Error(`Errore ${response.status}`)
      }
      const data = await response.json()
      setBook(data.book)
      setCourseName(data.course_name || data.course?.name || '')
      setError('')
    } catch (err) {
      console.error('Errore caricamento libro:', err)
      setError('Impossibile caricare il libro selezionato')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[MindmapClient] init', { effectiveCourseId, effectiveBookId })
    }
    if (effectiveCourseId && effectiveBookId) {
      loadBookInfo()

      const saved = mindmapService.getSavedMindmap(effectiveCourseId, effectiveBookId)
      if (saved?.mindmap) {
        setMindmap(saved.mindmap)
        setMarkdown(saved.markdown || '')
        setLastSavedAt(saved.createdAt)
      }
    }
  }, [effectiveCourseId, effectiveBookId])

  const handleGenerateMindmap = async () => {
    if (!effectiveCourseId || !effectiveBookId) return

    setGenerating(true)
    setError('')

    try {
      // Collect session context for enhanced generation
      const sessionContext = await collectSessionContext(effectiveCourseId, effectiveBookId)

      const requestBody: any = {
        course_id: effectiveCourseId,
        book_id: effectiveBookId,
        context_type: 'book'
      }

      // Add session context if available
      if (sessionContext) {
        requestBody.session_context = sessionContext
        console.log('🚀 Using enhanced mindmap generation with session context')
      }

      const response = await fetchFromBackend('/mindmap', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      const { payload, rawText } = await parseJsonSafely<MindmapGenerationResponse>(response)

      if (!response.ok || !payload?.success) {
        console.error('Errore generazione mindmap:', rawText || payload)
        throw new Error('Generazione mindmap fallita')
      }

      if (payload.mindmap && hasMindmapNodes(payload.mindmap)) {
        setMindmap(payload.mindmap)
      }
      setMarkdown(payload.markdown || '')
      setReferences(toStringArray(payload.references))
      setSources(toMindmapSources(payload.sources))

      // Enhanced feedback
      if (payload.enhanced || payload.session_aware) {
        toast.success('🧠 Mindmap avanzata generata con contesto personalizzato!', {
          duration: 4000,
          icon: '🎯'
        })
      } else {
        toast.success('Mindmap generata con successo!')
      }
    } catch (err) {
      console.error('Errore generazione mindmap:', err)
      setError('Impossibile generare la mindmap. Riprova più tardi.')
      toast.error('Errore durante la generazione')
    } finally {
      setGenerating(false)
    }
  }

  const handleSaveMindmap = async (data: MindmapSaveInput) => {
    if (!effectiveCourseId || !effectiveBookId) return

    setSaving(true)

    try {
      const payload: MindmapStoragePayload = isStoragePayload(data)
        ? data
        : {
            title: 'Mindmap generata',
            structured_map: {
              title: 'Mindmap generata',
              nodes: Array.from((data as any).nodes?.values() || []) as StudyMindmapNode[],
              study_plan: []
            },
            content_markdown: (data as any).description || ''
          }

      await mindmapService.saveMindmap(effectiveCourseId, effectiveBookId, payload)
      setLastSavedAt(new Date().toISOString())
      toast.success('Mindmap salvata!')
    } catch (err) {
      console.error('Errore salvataggio mindmap:', err)
      toast.error('Salvataggio fallito')
    } finally {
      setSaving(false)
    }
  }

  if (!effectiveCourseId || !effectiveBookId) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-gray-600 mb-4">URL non valido</p>
          <Link href="/courses" className="text-blue-600 hover:text-blue-700">
            ← Torna ai corsi
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push(`/courses/${effectiveCourseId}/books/${effectiveBookId}`)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div>
              <p className="text-sm text-gray-500">{courseName}</p>
              <h1 className="text-2xl font-bold text-gray-900">Mappa Concettuale</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateMindmap}
              disabled={generating}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generazione in corso...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Rigenera Mindmap
                </>
              )}
            </button>

            <button
              onClick={() => mindmap && handleSaveMindmap({ structured_map: mindmap, content_markdown: markdown })}
              disabled={!mindmap || saving}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Salvataggio...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Salva
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {lastSavedAt && (
          <div className="mb-4 text-sm text-gray-500">
            Ultimo salvataggio: {new Date(lastSavedAt).toLocaleString()}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center min-h-[50vh]">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-3" />
              <p className="text-gray-600">Caricamento informazioni libro...</p>
            </div>
          </div>
        ) : (
          <>
            {mindmap ? (
              <VisualMindmap data={mindmap as any} />
            ) : (
              <div className="text-center py-16">
                <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Nessuna mindmap disponibile
                </h3>
                <p className="text-gray-600 mb-6">
                  Genera una nuova mappa concettuale per questo libro
                </p>
                <button
                  onClick={handleGenerateMindmap}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                >
                  <Sparkles className="h-4 w-4" />
                  Genera mindmap
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
              <div className="lg:col-span-2">
                {mindmap ? (
                  <MindmapExplorer mindmap={mindmap} />
                ) : (
                  <div className="p-6 bg-white border rounded-xl text-center text-gray-500">
                    Genera o seleziona una mindmap per utilizzare l'esploratore.
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div className="bg-white p-4 rounded-xl shadow-sm border space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-blue-500" />
                    Libro di riferimento
                  </h3>
                  <div className="text-sm text-gray-600">
                    <p className="font-medium text-gray-900">{book?.title}</p>
                    <p>{book?.author}</p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl shadow-sm border space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    Suggerimenti
                  </h3>
                  <ul className="text-sm text-gray-600 space-y-2 list-disc list-inside">
                    <li>Usa il pannello a destra per espandere i nodi chiave</li>
                    <li>Puoi salvare modifiche manuali alla mappa</li>
                    <li>Rigenera la mindmap dopo aver aggiunto nuovi materiali</li>
                  </ul>
                </div>

                <div className="bg-white p-4 rounded-xl shadow-sm border space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <FileText className="h-5 w-5 text-green-500" />
                    Fonti utilizzate
                  </h3>
                  {sources.length === 0 ? (
                    <p className="text-sm text-gray-500">Genera la mindmap per vedere le fonti.</p>
                  ) : (
                    <ul className="text-sm text-gray-600 space-y-1">
                      {sources.map((source, index) => (
                        <li key={index}>
                          {typeof source === 'string'
                            ? source
                            : source.source || `Fonte ${index + 1}`}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
