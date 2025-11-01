'use client'

import { useState, useEffect } from 'react'
import { Brain, FileText, CheckCircle, AlertCircle, RefreshCw, Play, BarChart3 } from 'lucide-react'
import { useContentIndexing } from '@/hooks/useContentIndexing'
import { MaterialIndexingStatus, ContentAnalysisResult } from '@/types/indexing'

interface MaterialIndexingPanelProps {
  materialId: string
  materialName: string
  onIndexingComplete?: () => void
}

export function MaterialIndexingPanel({
  materialId,
  materialName,
  onIndexingComplete
}: MaterialIndexingPanelProps) {
  const {
    indexingStatus,
    analysisResult,
    isIndexing,
    startIndexing,
    checkIndexingStatus,
    retryIndexing,
    clearIndexingStatus
  } = useContentIndexing()

  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    if (materialId) {
      checkIndexingStatus(materialId)
    }
  }, [materialId, checkIndexingStatus])

  useEffect(() => {
    if (indexingStatus?.status === 'completed' && onIndexingComplete) {
      onIndexingComplete()
    }
  }, [indexingStatus?.status, onIndexingComplete])

  const getStatusIcon = () => {
    switch (indexingStatus?.status) {
      case 'processing':
        return <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Brain className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (indexingStatus?.status) {
      case 'processing':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getProgressPercentage = () => {
    if (!indexingStatus || indexingStatus.total_chunks === 0) return 0
    return Math.round((indexingStatus.processed_chunks / indexingStatus.total_chunks) * 100)
  }

  return (
    <div className="glass rounded-2xl p-6 border border-gray-200/50">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className={`p-3 rounded-xl ${getStatusColor()}`}>
            {getStatusIcon()}
          </div>
          <div>
            <h3 className="font-semibold text-lg text-gray-900">
              Indicizzazione Contenuti
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {materialName}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {!indexingStatus || indexingStatus.status === 'failed' ? (
            <button
              onClick={() => materialId && startIndexing(materialId)}
              disabled={isIndexing}
              className="btn btn-primary btn-sm"
            >
              <Play className="h-4 w-4 mr-2" />
              Inizia Indicizzazione
            </button>
          ) : indexingStatus.status === 'processing' ? (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Elaborazione...</span>
            </div>
          ) : indexingStatus.status === 'failed' ? (
            <button
              onClick={() => materialId && retryIndexing(materialId)}
              disabled={isIndexing}
              className="btn btn-secondary btn-sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Riprova
            </button>
          ) : (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="btn btn-ghost btn-sm"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Dettagli
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {indexingStatus && indexingStatus.status === 'processing' && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Progresso Indicizzazione
            </span>
            <span className="text-sm text-gray-500">
              {getProgressPercentage()}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Status Details */}
      {indexingStatus && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {indexingStatus.processed_chunks}
            </div>
            <p className="text-sm text-gray-500">Chunk processati</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {indexingStatus.extracted_concepts}
            </div>
            <p className="text-sm text-gray-500">Concetti estratti</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {indexingStatus.generated_questions}
            </div>
            <p className="text-sm text-gray-500">Test generati</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {Math.round((indexingStatus.generated_questions / indexingStatus.processed_chunks) * 10) / 10}
            </div>
            <p className="text-sm text-gray-500">Test per chunk</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {showDetails && analysisResult && (
        <div className="border-t border-gray-200 pt-6">
          <h4 className="font-semibold text-gray-900 mb-4">Analisi del Contenuto</h4>

          {/* Summary */}
          <div className="mb-6">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Riepilogo</h5>
            <p className="text-sm text-gray-600 leading-relaxed">
              {analysisResult.summary}
            </p>
          </div>

          {/* Key Concepts */}
          <div className="mb-6">
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Concetti Chiave ({analysisResult.key_concepts.length})
            </h5>
            <div className="flex flex-wrap gap-2">
              {analysisResult.key_concepts.map((concept, index) => (
                <span
                  key={index}
                  className="badge badge-primary text-xs"
                >
                  {concept}
                </span>
              ))}
            </div>
          </div>

          {/* Difficulty Distribution */}
          <div className="mb-6">
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Distribuzione Difficoltà
            </h5>
            <div className="flex items-center space-x-4">
              {Object.entries(analysisResult.difficulty_distribution).map(([level, count]) => (
                <div key={level} className="flex items-center space-x-2">
                  <span className="text-xs text-gray-600">Liv {level}:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2 min-w-[60px]">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{
                        width: `${Math.max(20, (count / Math.max(...Object.values(analysisResult.difficulty_distribution))) * 100)}%`
                      }}
                    ></div>
                  </div>
                  <span className="text-xs font-medium text-gray-700 w-8">
                    {count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Learning Objectives */}
          <div className="mb-6">
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Obiettivi di Apprendimento
            </h5>
            <ul className="space-y-1">
              {analysisResult.learning_objectives.map((objective, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  {objective}
                </li>
              ))}
            </ul>
          </div>

          {/* Prerequisites */}
          {analysisResult.prerequisite_concepts.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">
                Prerequisiti
              </h5>
              <div className="flex flex-wrap gap-2">
                {analysisResult.prerequisite_concepts.map((concept, index) => (
                  <span
                    key={index}
                    className="badge badge-warning text-xs"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {indexingStatus?.status === 'failed' && (
        <div className="alert alert-danger">
          <AlertCircle className="h-4 w-4 mr-2" />
          Errore nell'indicizzazione: {indexingStatus.error_message || 'Errore sconosciuto'}
        </div>
      )}
    </div>
  )
}