'use client'

import { useState, useEffect } from 'react'
import { Database, FileText, Search, Brain, Activity, CheckCircle, AlertCircle, Clock, Server, HardDrive, Zap, BarChart, RefreshCw, Settings } from 'lucide-react'

interface RAGStatus {
  status: string
  timestamp: string
  vector_db: {
    collection_name: string
    total_documents: number
    embedding_model: string
    model_loaded: boolean
  }
  system_info: {
    data_directory: string
    supported_formats: string[]
    chunk_size: number
    chunk_overlap: number
    similarity_metric: string
  }
}

interface DocumentStats {
  documents: Array<{
    source: string
    chunks: Array<{ index: number; content: string }>
    total_chunks: number
  }>
  total_sources: number
  course_id: string
}

interface CourseSummary {
  id: string
  name: string
  subject?: string
}

type CoursesResponse = {
  courses?: Array<{
    id: string
    name: string
    subject?: string
  }>
}

type RagStatusResponse = RAGStatus

export default function RAGStatusPage() {
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null)
  const [documentStats, setDocumentStats] = useState<DocumentStats | null>(null)
  const [courses, setCourses] = useState<CourseSummary[]>([])
  const [selectedCourse, setSelectedCourse] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reindexing, setReindexing] = useState(false)
  const [showModelSettings, setShowModelSettings] = useState(false)
  const availableModels = [
    'paraphrase-multilingual-MiniLM-L12-v2',
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
    'BAAI/bge-m3',
    'BAAI/bge-base-en',
    'BAAI/bge-large-en',
    'e5-mistral-7b-instruct'
  ]

  useEffect(() => {
    fetchRAGStatus()
    fetchCourses()
  }, [])

  const fetchRAGStatus = async () => {
    try {
      setError(null)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/rag/status`)
      if (response.ok) {
        const data: RagStatusResponse = await response.json()
        setRagStatus(data)
      } else {
        throw new Error('Failed to fetch RAG status')
      }
    } catch (error) {
      console.error('Error fetching RAG status:', error)
      setError('Errore nel caricamento dello stato del RAG')
    } finally {
      setLoading(false)
    }
  }

  const fetchCourses = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses`)
      if (response.ok) {
        const data: CoursesResponse = await response.json()
        const courseList: CourseSummary[] = Array.isArray(data.courses)
          ? data.courses
              .filter((course): course is { id: string; name: string; subject?: string } => Boolean(course?.id))
              .map((course) => ({
                id: course.id,
                name: course.name ?? 'Corso',
                subject: course.subject
              }))
          : []
        setCourses(courseList)
        if (courseList.length > 0) {
          setSelectedCourse(courseList[0].id)
        }
      }
    } catch (error) {
      console.error('Error fetching courses:', error)
    }
  }

  const fetchDocumentStats = async () => {
    if (!selectedCourse) return

    try {
      const url = searchQuery
        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/rag/documents/${selectedCourse}?search_query=${encodeURIComponent(searchQuery)}`
        : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/rag/documents/${selectedCourse}`

      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setDocumentStats(data)
      }
    } catch (error) {
      console.error('Error fetching document stats:', error)
    }
  }

  useEffect(() => {
    fetchDocumentStats()
  }, [selectedCourse, searchQuery])

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('it-IT')
  }

  const reindexWithNewModel = async (newModel: string) => {
    if (!selectedCourse) return

    setReindexing(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/rag/reindex`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: selectedCourse,
          new_model: newModel
        })
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Reindex completed:', data)
        await fetchRAGStatus()
        await fetchDocumentStats()
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Reindexing failed')
      }
    } catch (error) {
      console.error('Error reindexing:', error)
      setError(`Reindicizzazione fallita: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`)
    } finally {
      setReindexing(false)
    }
  }

  const deleteAllIndexData = async () => {
    if (!selectedCourse) return

    if (!confirm('Sei sicuro di voler eliminare tutti i dati indicizzati? Questa operazione non è reversibile.')) {
      return
    }

    setReindexing(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/rag/clear-index/${selectedCourse}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        console.log('Index cleared successfully')
        await fetchRAGStatus()
        await fetchDocumentStats()
      } else {
        throw new Error('Failed to clear index')
      }
    } catch (error) {
      console.error('Error clearing index:', error)
      setError(`Eliminazione indice fallita: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`)
    } finally {
      setReindexing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !ragStatus) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {error || 'Errore nel caricamento'}
        </h2>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Sistema RAG
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          Retrieval-Augmented Generation - Monitoraggio Stato e Performance
        </p>

        {/* Status Overview */}
        <div className="flex items-center justify-center space-x-3 mb-8">
          {ragStatus.status === 'healthy' ? (
            <>
              <CheckCircle className="h-6 w-6 text-green-500" />
              <span className="text-lg font-medium text-green-700">Sistema Operativo</span>
            </>
          ) : (
            <>
              <AlertCircle className="h-6 w-6 text-red-500" />
              <span className="text-lg font-medium text-red-700">Sistema in Errore</span>
            </>
          )}
          <span className="text-sm text-gray-500 ml-4">
            Aggiornato: {formatTimestamp(ragStatus.timestamp)}
          </span>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Vector Database Status */}
        <div className="glass-card rounded-xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <Database className="h-8 w-8 text-blue-600" />
            {ragStatus.vector_db.model_loaded ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            )}
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Vector Database</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Documenti:</span>
              <span className="font-medium">{ragStatus.vector_db.total_documents}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Collection:</span>
              <span className="font-medium text-xs">{ragStatus.vector_db.collection_name}</span>
            </div>
          </div>
        </div>

        {/* Embedding Model */}
        <div className="glass-card rounded-xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <Brain className="h-8 w-8 text-purple-600" />
            <div className="flex items-center space-x-1">
              <div className={`h-2 w-2 rounded-full ${ragStatus.vector_db.model_loaded ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
              <span className="text-xs text-gray-500">
                {ragStatus.vector_db.model_loaded ? 'Loaded' : 'Lazy'}
              </span>
            </div>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Modello Embedding</h3>
          <p className="text-sm text-gray-600 mb-1">{ragStatus.vector_db.embedding_model}</p>
          <p className="text-xs text-gray-500 mb-3">Multilingual MiniLM-L12</p>

          {/* Model Management Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setShowModelSettings(!showModelSettings)}
              disabled={reindexing || !selectedCourse}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              <Settings className="h-4 w-4" />
              <span>Cambia Modello</span>
            </button>

            <button
              onClick={() => reindexWithNewModel(ragStatus.vector_db.embedding_model)}
              disabled={reindexing || !selectedCourse}
              className="flex items-center space-x-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              {reindexing ? (
                <>
                  <div className="loading-spinner h-4 w-4"></div>
                  <span>Reindicizzando...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  <span>Reindicizza</span>
                </>
              )}
            </button>

            <button
              onClick={deleteAllIndexData}
              disabled={reindexing || !selectedCourse}
              className="flex items-center space-x-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              <AlertCircle className="h-4 w-4" />
              <span>Pulisci Indice</span>
            </button>
          </div>

          {/* Model Selection Modal */}
          {showModelSettings && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Seleziona Modello Embedding</h3>
                  <button
                    onClick={() => setShowModelSettings(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-3">
                  {availableModels.map((model) => (
                    <div
                      key={model}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        model === ragStatus.vector_db.embedding_model
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        reindexWithNewModel(model)
                        setShowModelSettings(false)
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{model}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {model.includes('multilingual') && '🌍 Multilingue'}
                            {model.includes('BGE') && '🚀 Alta Performance'}
                            {model.includes('e5') && '⚡ Avanzato'}
                          </p>
                        </div>
                        {model === ragStatus.vector_db.embedding_model && (
                          <CheckCircle className="h-5 w-5 text-blue-500" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    <strong>⚠️ Attenzione:</strong> La reindicizzazione richiederà tempo e ricreerà completamente
                    l'indice vettoriale con il nuovo modello. Tutti i dati esistenti verranno persi e ricreati.
                  </p>
                </div>

                <div className="flex justify-end mt-4">
                  <button
                    onClick={() => setShowModelSettings(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Annulla
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* System Configuration */}
        <div className="glass-card rounded-xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <Server className="h-8 w-8 text-green-600" />
            <Activity className="h-5 w-5 text-blue-500 animate-pulse" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Configurazione</h3>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Chunk size:</span>
              <span className="font-medium">{ragStatus.system_info.chunk_size}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Overlap:</span>
              <span className="font-medium">{ragStatus.system_info.chunk_overlap}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Metric:</span>
              <span className="font-medium">{ragStatus.system_info.similarity_metric}</span>
            </div>
          </div>
        </div>

        {/* Supported Formats */}
        <div className="glass-card rounded-xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <FileText className="h-8 w-8 text-orange-600" />
            <Zap className="h-5 w-5 text-yellow-500" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Formati Supportati</h3>
          <div className="flex flex-wrap gap-1">
            {ragStatus.system_info.supported_formats.map((format, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
              >
                {format}
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Directory: {ragStatus.system_info.data_directory}
          </p>
        </div>
      </div>

      {/* Documents Analysis Section */}
      <div className="glass-card rounded-xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <BarChart className="h-6 w-6 mr-3 text-blue-600" />
            Analisi Documenti Indicizzati
          </h2>

          {/* Course Selector */}
          <div className="flex items-center space-x-4">
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Seleziona corso...</option>
              {courses.map(course => (
                <option key={course.id} value={course.id}>
                  {course.name} ({course.subject})
                </option>
              ))}
            </select>

            {/* Search */}
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Cerca nei documenti..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {documentStats ? (
          <div className="space-y-6">
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <FileText className="h-6 w-6 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-blue-900">Sorgenti Uniche</p>
                    <p className="text-2xl font-bold text-blue-900">{documentStats.total_sources}</p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <HardDrive className="h-6 w-6 text-green-600" />
                  <div>
                    <p className="text-sm font-medium text-green-900">Total Chunks</p>
                    <p className="text-2xl font-bold text-green-900">
                      {documentStats.documents.reduce((acc, doc) => acc + doc.total_chunks, 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Clock className="h-6 w-6 text-purple-600" />
                  <div>
                    <p className="text-sm font-medium text-purple-900">Corso ID</p>
                    <p className="text-sm font-mono text-purple-900">{documentStats.course_id}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Documents List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Documenti Indicizzati</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {documentStats.documents.map((doc, index) => (
                  <div
                    key={index}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="font-medium text-gray-900 truncate flex-1">{doc.source}</h4>
                      <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full ml-2">
                        {doc.total_chunks} chunks
                      </span>
                    </div>

                    {/* Sample Chunks */}
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">Anteprima contenuti:</p>
                      <div className="space-y-1">
                        {doc.chunks.slice(0, 2).map((chunk, chunkIndex) => (
                          <div
                            key={chunkIndex}
                            className="bg-gray-50 rounded p-2 text-xs text-gray-700"
                          >
                            <span className="font-medium text-blue-600">Chunk {chunk.index}:</span>{' '}
                            {chunk.content}
                          </div>
                        ))}
                        {doc.chunks.length > 2 && (
                          <p className="text-xs text-gray-500 italic">
                            ... e altri {doc.chunks.length - 2} chunks
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p>Seleziona un corso per vedere i documenti indicizzati</p>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      <div className="glass-card rounded-xl p-6 border border-gray-200/50">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Activity className="h-6 w-6 mr-3 text-green-600" />
          Metriche di Performance e Best Practices
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* RAG Optimization Tips */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Consigli per Ottimizzazione RAG</h3>
            <ul className="space-y-3 text-sm text-gray-700">
              <li className="flex items-start space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span><strong>Chunking intelligente:</strong> I chunk di 1000 token con overlap del 20% ottimizzano contesto e performance</span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span><strong>Lazy loading:</strong> Il modello embedding viene caricato solo quando necessario per ridurre l'uso di RAM</span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span><strong>Cosine similarity:</strong> Metrica ottimale per confronti semantici in documenti multilingua</span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span><strong>Preprocessing PDF:</strong> Utilizzo di PyMuPDF con fallback a PyPDF2 per massima compatibilità</span>
              </li>
            </ul>
          </div>

          {/* System Health */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Stato del Sistema</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-green-900">Vector Database</span>
                <span className="text-sm text-green-700">Operativo</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-green-900">Embedding Model</span>
                <span className="text-sm text-green-700">Disponibile</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-blue-900">Document Processing</span>
                <span className="text-sm text-blue-700">Ready</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                <span className="text-sm font-medium text-yellow-900">Storage</span>
                <span className="text-sm text-yellow-700">Locale</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
