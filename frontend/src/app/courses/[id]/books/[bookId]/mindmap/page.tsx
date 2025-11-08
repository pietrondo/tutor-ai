'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Brain, RefreshCw, Loader2, Save, BookOpen, Sparkles, FileText, Lightbulb } from 'lucide-react'
import toast from 'react-hot-toast'
import { MindmapExplorer } from '@/components/MindmapExplorer'
import { StudyMindmap, StudyMindmapNode, ExpandedStudyNode } from '@/types/mindmap'
import VisualMindmap, { type MindmapData } from '@/components/VisualMindmap'
import { mindmapService, type MindmapStorage } from '@/services/mindmapService'

const normalizeApiBaseUrl = (value: string) => {
  if (value === '/') return '/'
  return value.endsWith('/') ? value.slice(0, -1) : value
}

const API_BASE_URL = normalizeApiBaseUrl(process.env.NEXT_PUBLIC_API_URL ?? '/api')
const buildApiUrl = (path: string) => `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`

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

interface MindmapStoragePayload {
  title?: string
  structured_map?: StudyMindmap
  content_markdown?: string
  [key: string]: unknown
}

interface SavedMindmapEntry {
  id: string
  title: string
  data: MindmapStoragePayload
  createdAt: string
  courseId: string
  bookId: string
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

export default function MindmapPage() {
  const params = useParams()
  const courseIdFromParams = params.id as string
  const bookIdFromParams = params.bookId as string

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
  const [viewMode, setViewMode] = useState<'explorer' | 'visual'>('visual')
  const [savedMindmaps, setSavedMindmaps] = useState<SavedMindmapEntry[]>([])
  const [fromCache, setFromCache] = useState(false)

  // Load saved mindmaps from unified service on mount
  useEffect(() => {
    const savedMaps = mindmapService.getSavedMindmaps(courseIdFromParams, bookIdFromParams)
    setSavedMindmaps(savedMaps)
    console.log(`📚 Loaded ${savedMaps.length} saved mindmaps for course ${courseIdFromParams}, book ${bookIdFromParams}`)
  }, [courseIdFromParams, bookIdFromParams])

  const normalizeMindmapForStorage = (input: MindmapSaveInput): MindmapStoragePayload => {
    if (isStoragePayload(input)) {
      return {
        ...input,
        title: input.title ?? mindmap?.title ?? 'Mappa Concettuale'
      }
    }

    const fallbackPayload: MindmapStoragePayload = {
      title: mindmap?.title || 'Mappa Concettuale',
      content_markdown: markdown
    }

    if (mindmap) {
      fallbackPayload.structured_map = mindmap
    }

    fallbackPayload.visual_state = input
    return fallbackPayload
  }

  const handleSaveMindmap = (mindmapData: MindmapSaveInput) => {
    const normalized = normalizeMindmapForStorage(mindmapData)
    setSaving(true)
    try {
      const mindmapToSave: SavedMindmapEntry = {
        id: Date.now().toString(),
        title: normalized.title || 'Mappa Concettuale',
        data: normalized,
        createdAt: new Date().toISOString(),
        courseId: courseIdFromParams,
        bookId: bookIdFromParams
      }

      const updated = [...savedMindmaps, mindmapToSave]
      setSavedMindmaps(updated)
      localStorage.setItem(`mindmaps_${courseIdFromParams}_${bookIdFromParams}`, JSON.stringify(updated))
      setLastSavedAt(mindmapToSave.createdAt)
      toast.success('Mappa salvata localmente!')
    } catch (error) {
      console.error('Errore durante il salvataggio della mappa:', error)
      toast.error('Impossibile salvare la mappa')
    } finally {
      setSaving(false)
    }
  }

  const handleLoadMindmap = (mindmapId: string) => {
    const savedEntry = savedMindmaps.find(m => m.id === mindmapId)
    if (!savedEntry) return

    if (viewMode === 'visual') {
      toast.success('Mappa caricata in modalità visuale')
      return
    }

    const structured = savedEntry.data.structured_map
    if (structured && hasMindmapNodes(structured)) {
      setMindmap(structured)
    } else if (hasMindmapNodes(savedEntry.data)) {
      setMindmap(savedEntry.data)
    }
    setMarkdown(savedEntry.data.content_markdown || '')
    toast.success('Mappa caricata in modalità esploratore')
  }

  const handleDeleteMindmap = (mindmapId: string) => {
    const updated = savedMindmaps.filter(m => m.id !== mindmapId)
    setSavedMindmaps(updated)
    localStorage.setItem(`mindmaps_${courseIdFromParams}_${bookIdFromParams}`, JSON.stringify(updated))
    toast.success('Mappa eliminata')
  }

  const handleExportMindmap = (mindmapData: MindmapSaveInput) => {
    const normalized = normalizeMindmapForStorage(mindmapData)
    const filename = `mindmap_${new Date().toISOString().split('T')[0]}.json`
    const blob = new Blob([JSON.stringify(normalized, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('Mappa esportata!')
  }

  useEffect(() => {
    fetchBook()
    fetchCourseInfo()
  }, [courseIdFromParams, bookIdFromParams])

  const fetchBook = async () => {
    try {
      const response = await fetch(buildApiUrl(`/courses/${courseIdFromParams}/books/${bookIdFromParams}`))
      if (response.ok) {
        const data = await response.json()
        setBook(data.book)
      } else {
        setError('Errore nel caricamento del libro')
      }
    } catch {
      setError('Errore nel caricamento del libro')
    } finally {
      setLoading(false)
    }
  }

  const fetchCourseInfo = async () => {
    try {
      const response = await fetch(buildApiUrl(`/courses/${courseIdFromParams}`))
      if (response.ok) {
        const data = await response.json()
        setCourseName(data.course.name)
      }
    } catch (error) {
      console.error('Error fetching course info:', error)
    }
  }

  const generateMindmap = async () => {
    if (!book || book.materials.length === 0) {
      const message = 'Nessun materiale disponibile per generare la mappa concettuale'
      setError(message)
      toast.error(message)
      return
    }

    setGenerating(true)
    setError('')

    try {
      // Usa il servizio unificato per generare/ottenere la mappa
      const result = await mindmapService.getMindmap({
        courseId: courseIdFromParams,
        bookId: bookIdFromParams,
        topic: book.title || 'Contenuti del libro',
        focusAreas: ['capitoli principali', 'concetti chiave', 'temi centrali'],
        forceRegenerate: false // Usa cache se disponibile
      })

      if (result.mindmap) {
        setMindmap(result.mindmap)
        setMarkdown('') // Il servizio gestisce il markdown internamente
        const combinedReferences = toStringArray(result.mindmap.references || [])
        setReferences(combinedReferences)
        setSources([]) // Il servizio gestisce le fonti internamente
        setLastSavedAt(null)
        setFromCache(result.fromCache)

        const cacheMessage = result.fromCache ?
          'Mappa concettuale caricata dalla cache condivisa' :
          'Mappa concettuale generata con successo'
        toast.success(cacheMessage)

        console.log(`🎯 Mindmap ${result.fromCache ? 'from cache' : 'generated'} for course ${courseIdFromParams}, book ${bookIdFromParams}`)
      } else {
        const message = result.error || 'Errore durante la generazione della mappa concettuale'
        setError(message)
        toast.error(message)
      }
    } catch (error) {
      console.error('Errore generazione mappa unificata', error)
      const message = 'Errore durante la generazione della mappa concettuale'
      setError(message)
      toast.error(message)
    } finally {
      setGenerating(false)
    }
  }

  const updateMindmapWithChildren = (map: StudyMindmap, targetId: string, children: StudyMindmapNode[]) => {
    const normalizeTitle = (title: string) => title.trim().toLowerCase()
    const sortNodes = (nodes: StudyMindmapNode[]) =>
      [...nodes].sort((a, b) => {
        const priorityWeight = (node: StudyMindmapNode) =>
          typeof node.priority === 'number' ? node.priority : Number.MAX_SAFE_INTEGER
        const weightDiff = priorityWeight(a) - priorityWeight(b)
        if (weightDiff !== 0) return weightDiff
        return a.title.localeCompare(b.title, 'it', { sensitivity: 'base' })
      })

    const mergeChildren = (nodes: StudyMindmapNode[]): StudyMindmapNode[] =>
      nodes.map((node) => {
        if (node.id === targetId) {
          const existingIds = new Set(node.children.map((child) => child.id))
          const existingTitles = new Set(node.children.map((child) => normalizeTitle(child.title)))
          const mergedChildren = [...node.children]

          children.forEach((child) => {
            const titleKey = normalizeTitle(child.title)
            if (existingIds.has(child.id) || existingTitles.has(titleKey)) {
              return
            }
            mergedChildren.push(child)
            existingIds.add(child.id)
            existingTitles.add(titleKey)
          })

          return { ...node, children: sortNodes(mergedChildren) }
        }

        if (node.children.length > 0) {
          return { ...node, children: mergeChildren(node.children) }
        }

        return node
      })

    return {
      ...map,
      nodes: mergeChildren(map.nodes)
    }
  }

  const handleExpandNode = async (path: StudyMindmapNode[], customPrompt?: string) => {
    console.log('🎯 handleExpandNode called with path:', path.map(n => n.title), 'customPrompt:', customPrompt)
    console.log('🔍 Current mindmap state:', mindmap ? 'exists' : 'null')
    console.log('🔄 Initializing mindmap data...', { mindmap, viewMode })

    // Capture the current mindmap to avoid race conditions
    const currentMindmap = mindmap
    if (!currentMindmap) {
      console.warn('⚠️ No mindmap available for expansion')
      throw new Error('Nessuna mappa concettuale disponibile per l\'espansione')
    }

    const targetNode = path[path.length - 1]
    if (!targetNode) {
      console.warn('⚠️ No target node found in path')
      throw new Error('Nodo target non trovato per l\'espansione')
    }

    // Validate and sanitize custom prompt
    const sanitizedPrompt = customPrompt?.trim()
    if (sanitizedPrompt && sanitizedPrompt.length > 1000) {
      console.warn('⚠️ Custom prompt too long:', sanitizedPrompt.length)
      throw new Error('Il prompt personalizzato è troppo lungo (massimo 1000 caratteri)')
    }

    console.log('🎪 Expanding node:', targetNode.title, 'ID:', targetNode.id)

    try {
      // Usa il servizio unificato per espandere il nodo
      const nodeContext = path.slice(0, -1).map((node) => node.title)
      const result = await mindmapService.expandNode(
        courseIdFromParams,
        bookIdFromParams,
        targetNode.title,
        nodeContext,
        sanitizedPrompt
      )

      if (result) {
        console.log('🌱 Expanded nodes created:', result.expandedNodes.length, result.expandedNodes.map(n => n.title))

        if (result.expandedNodes.length === 0) {
          console.log('📭 No new concepts generated')
          toast('Nessun nuovo sotto-concetto generato')
          return
        }

        console.log('🔄 Updating mindmap with children...')
        setMindmap((prev) => {
          const updated = prev ? updateMindmapWithChildren(prev, targetNode.id, result.expandedNodes) : prev
          console.log('✅ Mindmap updated with', result.expandedNodes.length, 'new nodes')
          return updated
        })

        // Aggiorna referenze
        if (result.sources.length) {
          setReferences((prev) => Array.from(new Set([...prev, ...result.sources])))
        }

        toast.success(`Aggiunti ${result.expandedNodes.length} nuovi sotto-concetti`)
        console.log(`🎯 Node expanded via unified service for course ${courseIdFromParams}, book ${bookIdFromParams}`)
      } else {
        toast.error('Impossibile espandere il nodo con l\'AI')
      }
    } catch (error) {
      console.error('Errore durante l\'espansione del nodo', error)
      toast.error('Errore durante l\'espansione del nodo')
    }
  }

  const updateMindmapNode = (map: StudyMindmap, targetId: string, updatedNode: StudyMindmapNode): StudyMindmap => {
    const updateNode = (nodes: StudyMindmapNode[]): StudyMindmapNode[] =>
      nodes.map((node) => {
        if (node.id === targetId) {
          return { ...node, ...updatedNode }
        }
        if (node.children.length > 0) {
          return { ...node, children: updateNode(node.children) }
        }
        return node
      })

    return {
      ...map,
      nodes: updateNode(map.nodes)
    }
  }

  const handleEditNode = async (node: StudyMindmapNode, instruction: string) => {
    if (!mindmap) return

    try {
      const requestBody = {
        course_id: courseIdFromParams,
        book_id: bookIdFromParams,
        node_id: node.id,
        current_title: node.title,
        current_summary: node.summary || '',
        edit_instruction: instruction
      }

      const response = await fetch(buildApiUrl('/mindmap/edit'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      const { payload, rawText } = await parseJsonSafely<MindmapEditApiResponse>(response)

      if (response.ok && payload && payload.success && payload.edited_node) {
        const updatedNode: StudyMindmapNode = {
          id: payload.edited_node.id,
          title: payload.edited_node.title,
          summary: payload.edited_node.summary || '',
          ai_hint: payload.edited_node.ai_hint || '',
          study_actions: payload.edited_node.study_actions || [],
          priority: payload.edited_node.priority || null,
          references: payload.edited_node.references || [],
          children: node.children // Preserve existing children
        }

        setMindmap((prev) => prev ? updateMindmapNode(prev, node.id, updatedNode) : prev)

        const newReferences = toStringArray(payload.sources_used)
        if (newReferences.length) {
          setReferences((prev) => Array.from(new Set([...prev, ...newReferences])))
        }

        toast.success('Nodo modificato con successo')
      } else {
        const message =
          (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string'
            ? payload.detail
            : rawText || 'Impossibile modificare il nodo con l\'AI')
        toast.error(message)
      }
    } catch (error) {
      console.error('Errore durante la modifica del nodo', error)
      toast.error('Errore durante la modifica del nodo')
    }
  }

  const formatSourceLabel = (source: MindmapSource, index: number): string => {
    if (typeof source === 'string') {
      return source
    }
    const base =
      typeof source.source === 'string' && source.source.trim().length > 0
        ? source.source
        : `Fonte ${index + 1}`
    const chunkDetails =
      typeof source.chunk_index === 'number' ? ` • Chunk ${source.chunk_index + 1}` : ''
    const scoreDetails =
      typeof source.relevance_score === 'number'
        ? ` • Rilevanza ${source.relevance_score.toFixed(2)}`
        : ''
    return `${base}${chunkDetails}${scoreDetails}`.trim()
  }

  const handleDownloadMarkdown = () => {
    if (!markdown) {
      toast.error('Nessun contenuto da scaricare')
      return
    }
    const filename = `${(mindmap?.title || 'mappa-concettuale').replace(/[^a-z0-9]+/gi, '_').toLowerCase()}.md`
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Caricamento...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href={`/courses/${courseIdFromParams}/books/${bookIdFromParams}`}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </Link>
              <div>
                <nav className="text-sm text-gray-500 mb-1">
                  <Link href={`/courses/${courseIdFromParams}`} className="hover:text-gray-700">
                    {courseName}
                  </Link>
                  <span className="mx-2">/</span>
                  <Link href={`/courses/${courseIdFromParams}/books`} className="hover:text-gray-700">
                    Libri
                  </Link>
                  <span className="mx-2">/</span>
                  <Link href={`/courses/${courseIdFromParams}/books/${bookIdFromParams}`} className="hover:text-gray-700">
                    {book?.title}
                  </Link>
                  <span className="mx-2">/</span>
                  <span className="text-gray-900">Mappa Concettuale</span>
                </nav>
                <h1 className="text-2xl font-bold text-gray-900">Mappa Concettuale</h1>
                <p className="text-gray-600">{book?.title}</p>
              </div>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('visual')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'visual'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🧠 Visuale
              </button>
              <button
                onClick={() => setViewMode('explorer')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'explorer'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📋 Esploratore
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Saved Mindmaps Sidebar */}
        {savedMindmaps.length > 0 && (
          <div className="mb-6 bg-white rounded-xl border p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">📚 Mappe Salvate</h3>
              <span className="text-sm text-gray-500">{savedMindmaps.length} mappe</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {savedMindmaps.map((saved) => (
                <div key={saved.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900 truncate">{saved.title}</h4>
                    <p className="text-xs text-gray-500">
                      {new Date(saved.createdAt).toLocaleDateString('it-IT')}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => handleLoadMindmap(saved.id)}
                      className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                      title="Carica mappa"
                    >
                      📂
                    </button>
                    <button
                      onClick={() => handleDeleteMindmap(saved.id)}
                      className="p-1 text-red-600 hover:bg-red-100 rounded"
                      title="Elimina mappa"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {viewMode === 'visual' ? (
          !mindmap ? (
            <div className="text-center py-20 bg-white rounded-xl border" style={{ height: '800px' }}>
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Brain className="h-10 w-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Genera Mappa Concettuale
              </h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Crea una mappa concettuale interattiva basata sui contenuti del libro utilizzando l'intelligenza artificiale.
              </p>
              <button
                onClick={generateMindmap}
                disabled={generating}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2 mx-auto"
              >
                {generating ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Generazione in corso...</span>
                  </>
                ) : (
                  <>
                    <Brain className="h-5 w-5" />
                    <span>Genera Mappa Concettuale</span>
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl border overflow-hidden" style={{ height: '800px' }}>
              <VisualMindmap
                data={mindmap}
                onSave={handleSaveMindmap}
                onExport={handleExportMindmap}
                editable={true}
                onExpandNode={handleExpandNode}
                className="w-full h-full"
              />
            </div>
          )
        ) : !mindmap ? (
          <div className="text-center py-20 bg-white rounded-xl border">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Brain className="h-10 w-10 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Genera Mappa Concettuale
            </h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Crea una mappa concettuale interattiva basata sui contenuti del libro utilizzando l'intelligenza artificiale.
            </p>
            <button
              onClick={generateMindmap}
              disabled={generating}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2 mx-auto"
            >
              {generating ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Generazione in corso...</span>
                </>
              ) : (
                <>
                  <Brain className="h-5 w-5" />
                  <span>Genera Mappa Concettuale</span>
                </>
              )}
            </button>
          </div>
        ) : mindmap ? (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Mappa concettuale generata</h2>
                {lastSavedAt && (
                  <p className="text-xs text-gray-500 mt-1">
                    Salvata il {new Date(lastSavedAt).toLocaleString('it-IT')}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={generateMindmap}
                  disabled={generating}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  <span>Rigenera</span>
                </button>
                <button
                  onClick={() => handleSaveMindmap({ structured_map: mindmap, content_markdown: markdown, title: mindmap.title })}
                  disabled={saving}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  <span>Salva localmente</span>
                </button>
                <button
                  onClick={handleDownloadMarkdown}
                  disabled={!markdown}
                  className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 flex items-center gap-2"
                >
                  <FileText className="h-4 w-4" />
                  <span>Esporta Markdown</span>
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl border p-6">
              <MindmapExplorer mindmap={mindmap} onExpandNode={handleExpandNode} onEditNode={handleEditNode} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border p-6">
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Contenuto testuale</h3>
                </div>
                <pre className="whitespace-pre-wrap text-gray-700 bg-gray-50 p-4 rounded-lg overflow-auto max-h-80 text-sm">
                  {markdown}
                </pre>
              </div>
              <div className="bg-white rounded-xl border p-6 space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-4 w-4 text-purple-600" />
                    <h3 className="text-lg font-semibold text-gray-900">Suggerimenti AI globali</h3>
                  </div>
                  <p className="text-sm text-gray-600">
                    Usa i pulsanti &quot;Espandi&quot; vicino ai nodi per generare sotto-concetti mirati con il supporto AI e integrare le attività nel tuo piano di studio.
                  </p>
                </div>
                {references.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">Riferimenti principali</h4>
                    <div className="flex flex-wrap gap-2">
                      {references.map((reference, index) => (
                        <span
                          key={`${reference}-${index}`}
                          className="px-3 py-1 bg-blue-50 border border-blue-100 text-blue-700 text-xs rounded-full"
                        >
                          {reference}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {sources.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">Fonti consultate</h4>
                    <ul className="space-y-1 text-xs text-gray-600">
                      {sources.map((source, index) => (
                        <li key={`${formatSourceLabel(source, index)}-${index}`} className="flex items-start gap-2">
                          <Lightbulb className="h-3 w-3 mt-1 text-amber-500" />
                          <span>{formatSourceLabel(source, index)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
