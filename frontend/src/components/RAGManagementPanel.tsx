'use client'

import { useState, useEffect } from 'react'
import {
  Database,
  Search,
  FileText,
  Upload,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Eye,
  BarChart3,
  Tag,
  Clock,
  TrendingUp,
  Zap,
  BookOpen,
  Settings,
  Trash2,
  Download
} from 'lucide-react'
import { llmManager } from '@/lib/llm-manager'

interface Document {
  id: string
  title: string
  content: string
  type: 'pdf' | 'text' | 'markdown' | 'webpage' | 'code'
  size: number
  source: string
  uploadDate: string
  lastModified: string
  courseId: string
  chunks: number
  indexed: boolean
  metadata: {
    author?: string
    language?: string
    tags: string[]
    difficulty?: number
    estimatedReadTime: number
  }
}

interface RAGSearchResult {
  query: string
  results: Array<{
    documentId: string
    documentTitle: string
    chunkId: string
    content: string
    relevanceScore: number
    source: string
    metadata: any
  }>
  searchTime: number
  totalResults: number
  vectorSearchTime: number
  rerankTime: number
}

interface RAGAnalytics {
  totalDocuments: number
  indexedChunks: number
  averageChunkSize: number
  totalSearches: number
  averageSearchTime: number
  hitRate: number
  popularQueries: Array<{
    query: string
    frequency: number
    avgRelevanceScore: number
  }>
  documentStats: Array<{
    type: string
    count: number
    totalSize: number
  }>
}

export function RAGManagementPanel() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<RAGSearchResult | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [isIndexing, setIsIndexing] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [analytics, setAnalytics] = useState<RAGAnalytics | null>(null)
  const [ragEnabled, setRagEnabled] = useState(true)
  const [chunkSettings, setChunkSettings] = useState({
    size: 1000,
    overlap: 200,
    strategy: 'fixed' as 'fixed' | 'semantic'
  })

  useEffect(() => {
    loadDocuments()
    loadAnalytics()
  }, [])

  const loadDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8000/rag/documents')
      if (response.ok) {
        const data = await response.json()
        // Transform backend data to frontend format
        const transformedDocuments = data.documents.map((doc: any, index: number) => ({
          id: `${doc.course_id}_${index}`,
          title: doc.source,
          content: doc.chunks[0]?.content || '',
          type: 'pdf' as const,
          size: doc.chunks.length * 1000, // Estimate size
          source: doc.source,
          uploadDate: new Date().toISOString(),
          lastModified: new Date().toISOString(),
          courseId: doc.course_id,
          chunks: doc.total_chunks || doc.chunks.length,
          indexed: true,
          metadata: {
            tags: ['imported'],
            estimatedReadTime: Math.ceil(doc.chunks.length * 2) // Estimate read time
          }
        }))
        setDocuments(transformedDocuments)
      } else {
        setDocuments([])
      }
    } catch (error) {
      console.error('Error loading documents:', error)
      setDocuments([])
    }
  }

  const loadAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8000/rag/analytics')
      if (response.ok) {
        const data = await response.json()
        // Transform backend data to frontend format
        const analytics: RAGAnalytics = {
          totalDocuments: data.analytics.total_documents || 0,
          indexedChunks: data.analytics.total_documents || 0, // Using total documents as chunks for now
          averageChunkSize: 1000,
          totalSearches: 0,
          averageSearchTime: 0,
          hitRate: 1.0,
          popularQueries: [],
          documentStats: [
            { type: 'pdf', count: data.analytics.total_documents || 0, totalSize: 0 }
          ]
        }
        setAnalytics(analytics)
      } else {
        setAnalytics(null)
      }
    } catch (error) {
      console.error('Error loading analytics:', error)
      setAnalytics(null)
    }
  }

  const handleFileUpload = async (files: FileList) => {
    const formData = new FormData()
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })

    try {
      setIsIndexing(true)
      const response = await fetch('/api/rag/upload', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Upload successful:', result)
        loadDocuments()
        loadAnalytics()
      }
    } catch (error) {
      console.error('Error uploading files:', error)
    } finally {
      setIsIndexing(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setSearchResults(null)

    try {
      const response = await fetch('/api/rag/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: searchQuery,
          limit: 5,
          includeMetadata: true,
          rerank: true
        })
      })

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data)
        loadAnalytics() // Update analytics
      } else {
        // Show demo message for missing API
        setSearchResults({
          query: searchQuery,
          results: [
            {
              documentId: '1',
              documentTitle: 'Esempio di documento RAG',
              chunkId: 'chunk-1',
              content: `Questo è un risultato di esempio per la ricerca: "${searchQuery}". Le API RAG non sono ancora implementate nel backend.`,
              relevanceScore: 0.85,
              source: 'demo-document',
              metadata: { type: 'demo', tags: ['esempio'] }
            }
          ],
          searchTime: 150,
          totalResults: 1,
          vectorSearchTime: 100,
          rerankTime: 50
        })
      }
    } catch (error) {
      console.error('Error performing search:', error)
      // Show demo results even on error
      setSearchResults({
        query: searchQuery,
        results: [
          {
            documentId: '1',
            documentTitle: 'Esempio di documento RAG',
            chunkId: 'chunk-1',
            content: `Questo è un risultato di esempio per la ricerca: "${searchQuery}". Le API RAG non sono ancora implementate nel backend.`,
            relevanceScore: 0.85,
            source: 'demo-document',
            metadata: { type: 'demo', tags: ['esempio'] }
          }
        ],
        searchTime: 150,
        totalResults: 1,
        vectorSearchTime: 100,
        rerankTime: 50
      })
    } finally {
      setIsSearching(false)
    }
  }

  const handleReindex = async (documentId: string) => {
    try {
      setIsIndexing(true)
      const response = await fetch(`/api/rag/documents/${documentId}/reindex`, {
        method: 'POST'
      })

      if (response.ok) {
        loadDocuments()
      }
    } catch (error) {
      console.error('Error reindexing document:', error)
    } finally {
      setIsIndexing(false)
    }
  }

  const handleDelete = async (documentId: string) => {
    if (!confirm('Sei sicuro di voler eliminare questo documento?')) return

    try {
      const response = await fetch(`/api/rag/documents/${documentId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        loadDocuments()
        loadAnalytics()
        if (selectedDocument?.id === documentId) {
          setSelectedDocument(null)
        }
      }
    } catch (error) {
      console.error('Error deleting document:', error)
    }
  }

  const getDocumentTypeIcon = (type: Document['type']) => {
    switch (type) {
      case 'pdf':
        return <FileText className="h-4 w-4 text-red-600" />
      case 'markdown':
        return <FileText className="h-4 w-4 text-purple-600" />
      case 'code':
        return <FileText className="h-4 w-4 text-blue-600" />
      case 'webpage':
        return <Eye className="h-4 w-4 text-green-600" />
      default:
        return <FileText className="h-4 w-4 text-gray-600" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-blue-600 bg-blue-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-gray-600 bg-gray-50'
  }

  return (
    <div className="space-y-6">
      {/* API Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-yellow-800">API RAG in sviluppo</h4>
            <p className="text-sm text-yellow-700 mt-1">
              Le API RAG non sono ancora implementate nel backend. I dati mostrati sono demo a scopo illustrativo.
            </p>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <Database className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Sistema RAG (Retrieval-Augmented Generation)
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Gestione documenti e ricerca semantica per risposte accurate
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={ragEnabled}
                onChange={(e) => setRagEnabled(e.target.checked)}
                className="form-checkbox"
              />
              <span className="text-sm text-gray-700">RAG Attivo</span>
            </label>
            <button
              onClick={() => loadDocuments()}
              className="btn btn-secondary btn-sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Aggiorna
            </button>
          </div>
        </div>

        {/* Analytics Overview */}
        {analytics && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-xl font-bold text-gray-900">{analytics.totalDocuments}</div>
              <p className="text-xs text-gray-600">Documenti</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600">{analytics.indexedChunks}</div>
              <p className="text-xs text-gray-600">Chunk indicizzati</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xl font-bold text-green-600">{analytics.totalSearches}</div>
              <p className="text-xs text-gray-600">Ricerche totali</p>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-xl font-bold text-purple-600">
                {analytics.averageSearchTime.toFixed(0)}ms
              </div>
              <p className="text-xs text-gray-600">Tempo medio</p>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-xl font-bold text-orange-600">
                {Math.round(analytics.hitRate * 100)}%
              </div>
              <p className="text-xs text-gray-600">Hit rate</p>
            </div>
          </div>
        )}
      </div>

      {/* Search Interface */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Ricerca Semantica</h4>
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Cerca nei documenti indicizzati..."
              className="form-input pl-10"
              disabled={!ragEnabled}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={!ragEnabled || isSearching || !searchQuery.trim()}
            className="btn btn-primary"
          >
            {isSearching ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Search className="h-4 w-4 mr-2" />
            )}
            Cerca
          </button>
        </div>

        {!ragEnabled && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center space-x-2 text-sm text-yellow-800">
              <AlertCircle className="h-4 w-4" />
              <span>RAG è attualmente disattivato. Abilitalo per cercare nei documenti.</span>
            </div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {searchResults && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">
              Risultati Ricerca ({searchResults.totalResults} trovati)
            </h4>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Tempo: {searchResults.searchTime}ms</span>
              <span>Vector: {searchResults.vectorSearchTime}ms</span>
              <span>Rerank: {searchResults.rerankTime}ms</span>
            </div>
          </div>

          <div className="space-y-4 max-h-96 overflow-y-auto">
            {searchResults.results.map((result, index) => (
              <div key={`${result.documentId}-${result.chunkId}`} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-gray-900">{result.documentTitle}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRelevanceColor(result.relevanceScore)}`}>
                        Score: {(result.relevanceScore * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">Fonte: {result.source}</p>
                  </div>
                  <div className="text-xs text-gray-500">
                    Chunk {index + 1}
                  </div>
                </div>
                <div className="text-sm text-gray-700 leading-relaxed bg-white p-3 rounded border">
                  {result.content}
                </div>
                {result.metadata && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(result.metadata).map(([key, value]) => (
                      <span key={key} className="badge badge-secondary text-xs">
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Management */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900">Documenti Indicizzati</h4>
          <div className="flex items-center space-x-2">
            <label className="btn btn-secondary btn-sm cursor-pointer">
              <Upload className="h-4 w-4 mr-2" />
              Carica Documenti
              <input
                type="file"
                multiple
                accept=".pdf,.txt,.md,.js,.ts,.jsx,.tsx,.html,.css"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                className="hidden"
              />
            </label>
          </div>
        </div>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 ${
                selectedDocument?.id === doc.id
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedDocument(doc)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3 flex-1">
                  {getDocumentTypeIcon(doc.type)}
                  <div className="flex-1">
                    <h5 className="font-medium text-gray-900">{doc.title}</h5>
                    <p className="text-sm text-gray-600 mt-1">{doc.source}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>{formatFileSize(doc.size)}</span>
                      <span>{doc.chunks} chunks</span>
                      <span>{new Date(doc.uploadDate).toLocaleDateString()}</span>
                      {doc.indexed ? (
                        <span className="flex items-center space-x-1 text-green-600">
                          <CheckCircle className="h-3 w-3" />
                          <span>Indicizzato</span>
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-yellow-600">
                          <AlertCircle className="h-3 w-3" />
                          <span>Da indicizzare</span>
                        </span>
                      )}
                    </div>
                    {doc.metadata.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {doc.metadata.tags.map((tag, index) => (
                          <span key={index} className="badge badge-primary text-xs">
                            <Tag className="h-3 w-3" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleReindex(doc.id)
                    }}
                    disabled={isIndexing}
                    className="btn btn-secondary btn-sm"
                  >
                    <RefreshCw className={`h-4 w-4 ${isIndexing ? 'animate-spin' : ''}`} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(doc.id)
                    }}
                    className="btn btn-ghost btn-sm text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Document Details */}
      {selectedDocument && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">Dettagli Documento</h4>
            <button
              onClick={() => setSelectedDocument(null)}
              className="btn btn-ghost btn-sm"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Titolo</span>
                <p className="font-medium text-gray-900">{selectedDocument.title}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Tipo</span>
                <p className="font-medium text-gray-900">{selectedDocument.type.toUpperCase()}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Dimensione</span>
                <p className="font-medium text-gray-900">{formatFileSize(selectedDocument.size)}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Chunk</span>
                <p className="font-medium text-gray-900">{selectedDocument.chunks}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Caricato il</span>
                <p className="font-medium text-gray-900">
                  {new Date(selectedDocument.uploadDate).toLocaleDateString()}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Stato</span>
                <p className="font-medium text-gray-900">
                  {selectedDocument.indexed ? 'Indicizzato' : 'Da indicizzare'}
                </p>
              </div>
            </div>

            {selectedDocument.metadata.tags.length > 0 && (
              <div>
                <span className="text-sm text-gray-600">Tags</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {selectedDocument.metadata.tags.map((tag, index) => (
                    <span key={index} className="badge badge-primary">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {selectedDocument.metadata.estimatedReadTime && (
              <div>
                <span className="text-sm text-gray-600">Tempo di lettura stimato</span>
                <p className="font-medium text-gray-900">
                  {selectedDocument.metadata.estimatedReadTime} minuti
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* RAG Settings */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-4">
          <Settings className="h-5 w-5 text-gray-600" />
          <h4 className="font-semibold text-gray-900">Impostazioni RAG</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dimensione Chunk
            </label>
            <input
              type="number"
              min="100"
              max="2000"
              step="100"
              value={chunkSettings.size}
              onChange={(e) => setChunkSettings(prev => ({ ...prev, size: parseInt(e.target.value) }))}
              className="form-input"
            />
            <p className="text-xs text-gray-500 mt-1">
              Caratteri per chunk
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sovrapposizione
            </label>
            <input
              type="number"
              min="0"
              max="500"
              step="50"
              value={chunkSettings.overlap}
              onChange={(e) => setChunkSettings(prev => ({ ...prev, overlap: parseInt(e.target.value) }))}
              className="form-input"
            />
            <p className="text-xs text-gray-500 mt-1">
              Caratteri di sovrapposizione
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Strategia Chunking
            </label>
            <select
              value={chunkSettings.strategy}
              onChange={(e) => setChunkSettings(prev => ({ ...prev, strategy: e.target.value as any }))}
              className="form-input"
            >
              <option value="fixed">Dimensione Fissa</option>
              <option value="semantic">Semantico</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Metodo di divisione del testo
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}