'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  RefreshCw,
  ArrowUpDown,
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Brain,
  Zap,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Activity,
  Database,
  Cloud
} from 'lucide-react'
import { useContentIndexing } from '@/hooks/useContentIndexing'
import { MaterialIndexingStatus, ContentAnalysisResult } from '@/types/indexing'

interface ContentSyncManagerProps {
  courseId: string
  materials: Array<{
    id: string
    name: string
    type: string
    size: number
    lastModified: string
    indexingStatus?: MaterialIndexingStatus
  }>
  onSyncComplete?: (materialId: string) => void
}

interface SyncOperation {
  id: string
  materialId: string
  materialName: string
  type: 'index' | 'reindex' | 'update'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  startedAt?: string
  completedAt?: string
  errorMessage?: string
}

interface AutoSyncConfig {
  enabled: boolean
  interval: number // minutes
  onlyUnindexed: boolean
  batchSize: number
  retryFailed: boolean
}

export function ContentSyncManager({
  courseId,
  materials,
  onSyncComplete
}: ContentSyncManagerProps) {
  const { startIndexing, retryIndexing, checkIndexingStatus, isIndexing } = useContentIndexing()

  const [syncOperations, setSyncOperations] = useState<SyncOperation[]>([])
  const [autoSyncConfig, setAutoSyncConfig] = useState<AutoSyncConfig>({
    enabled: false,
    interval: 30,
    onlyUnindexed: true,
    batchSize: 3,
    retryFailed: true
  })
  const [isAutoSyncing, setIsAutoSyncing] = useState(false)
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [activeTab, setActiveTab] = useState<'manual' | 'auto' | 'schedule'>('manual')

  useEffect(() => {
    // Load saved config
    const savedConfig = localStorage.getItem(`auto-sync-config-${courseId}`)
    if (savedConfig) {
      setAutoSyncConfig(JSON.parse(savedConfig))
    }

    const savedLastSync = localStorage.getItem(`last-sync-${courseId}`)
    if (savedLastSync) {
      setLastSyncTime(savedLastSync)
    }
  }, [courseId])

  useEffect(() => {
    // Save config
    localStorage.setItem(`auto-sync-config-${courseId}`, JSON.stringify(autoSyncConfig))
  }, [autoSyncConfig, courseId])

  useEffect(() => {
    if (autoSyncConfig.enabled && !isAutoSyncing) {
      const interval = setInterval(() => {
        checkForUpdatesAndSync()
      }, autoSyncConfig.interval * 60 * 1000)

      return () => clearInterval(interval)
    }
  }, [autoSyncConfig.enabled, autoSyncConfig.interval, isAutoSyncing])

  const checkForUpdatesAndSync = async () => {
    if (isAutoSyncing || isIndexing) return

    const materialsNeedingUpdate = materials.filter(material => {
      if (autoSyncConfig.onlyUnindexed) {
        return !material.indexingStatus || material.indexingStatus.status === 'failed'
      }
      return true
    })

    if (materialsNeedingUpdate.length > 0) {
      const batch = materialsNeedingUpdate.slice(0, autoSyncConfig.batchSize)
      await startBatchSync(batch, 'auto')
    }
  }

  const startBatchSync = async (batch: typeof materials, syncType: 'manual' | 'auto' = 'manual') => {
    setIsAutoSyncing(true)

    const operations = batch.map(material => ({
      id: `sync_${Date.now()}_${material.id}`,
      materialId: material.id,
      materialName: material.name,
      type: 'reindex' as const,
      status: 'pending' as const,
      progress: 0
    }))

    setSyncOperations(prev => [...prev, ...operations])

    for (const operation of operations) {
      setSyncOperations(prev =>
        prev.map(op => op.id === operation.id ? { ...op, status: 'running', startedAt: new Date().toISOString() } : op)
      )

      try {
        await retryIndexing(operation.materialId)

        // Monitor progress
        await monitorSyncProgress(operation.materialId, operation.id)

        setSyncOperations(prev =>
          prev.map(op => op.id === operation.id ? {
            ...op,
            status: 'completed',
            progress: 100,
            completedAt: new Date().toISOString()
          } : op)
        )

        if (onSyncComplete) {
          onSyncComplete(operation.materialId)
        }
      } catch (error) {
        setSyncOperations(prev =>
          prev.map(op => op.id === operation.id ? {
            ...op,
            status: 'failed',
            errorMessage: error instanceof Error ? error.message : 'Sync failed'
          } : op)
        )
      }
    }

    setLastSyncTime(new Date().toISOString())
    localStorage.setItem(`last-sync-${courseId}`, new Date().toISOString())
    setIsAutoSyncing(false)
  }

  const monitorSyncProgress = async (materialId: string, operationId: string) => {
    const checkProgress = async () => {
      try {
        await checkIndexingStatus(materialId)
        // Update progress based on indexing status
        setSyncOperations(prev =>
          prev.map(op => op.id === operationId ? { ...op, progress: Math.min(90, op.progress + 10) } : op)
        )
      } catch (error) {
        console.error('Error checking sync progress:', error)
      }
    }

    const interval = setInterval(checkProgress, 2000)
    setTimeout(() => clearInterval(interval), 30000) // Stop after 30 seconds
  }

  const manualSync = async (materialId: string) => {
    const material = materials.find(m => m.id === materialId)
    if (!material) return

    const operation: SyncOperation = {
      id: `sync_${Date.now()}_${materialId}`,
      materialId,
      materialName: material.name,
      type: 'reindex',
      status: 'pending',
      progress: 0
    }

    setSyncOperations(prev => [...prev, operation])

    try {
      setSyncOperations(prev =>
        prev.map(op => op.id === operation.id ? { ...op, status: 'running', startedAt: new Date().toISOString() } : op)
      )

      await retryIndexing(materialId)
      await monitorSyncProgress(materialId, operation.id)

      setSyncOperations(prev =>
        prev.map(op => op.id === operation.id ? {
          ...op,
          status: 'completed',
          progress: 100,
          completedAt: new Date().toISOString()
        } : op)
      )

      if (onSyncComplete) {
        onSyncComplete(materialId)
      }
    } catch (error) {
      setSyncOperations(prev =>
        prev.map(op => op.id === operation.id ? {
          ...op,
          status: 'failed',
          errorMessage: error instanceof Error ? error.message : 'Sync failed'
        } : op)
      )
    }
  }

  const clearCompletedOperations = () => {
    setSyncOperations(prev => prev.filter(op => op.status !== 'completed'))
  }

  const retryFailedOperations = async () => {
    const failedOps = syncOperations.filter(op => op.status === 'failed')
    const materialsToRetry = failedOps.map(op => materials.find(m => m.id === op.materialId)).filter(Boolean) as typeof materials

    if (materialsToRetry.length > 0) {
      await startBatchSync(materialsToRetry, 'manual')
    }
  }

  const getSyncStatusIcon = (status: SyncOperation['status']) => {
    switch (status) {
      case 'running':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: SyncOperation['status']) => {
    switch (status) {
      case 'running':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const renderManualSync = () => (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900">Sincronizzazione Manuale</h4>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => retryFailedOperations()}
              disabled={syncOperations.filter(op => op.status === 'failed').length === 0}
              className="btn btn-secondary btn-sm"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Riprova Falliti ({syncOperations.filter(op => op.status === 'failed').length})
            </button>
            <button
              onClick={clearCompletedOperations}
              disabled={syncOperations.filter(op => op.status === 'completed').length === 0}
              className="btn btn-ghost btn-sm"
            >
              Pulisci Completati
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="text-2xl font-bold text-blue-600">
              {materials.length}
            </div>
            <p className="text-sm text-gray-500">Totali Materiali</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="text-2xl font-bold text-green-600">
              {materials.filter(m => m.indexingStatus?.status === 'completed').length}
            </div>
            <p className="text-sm text-gray-500">Indicizzati</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="text-2xl font-bold text-orange-600">
              {materials.filter(m => !m.indexingStatus || m.indexingStatus.status === 'failed').length}
            </div>
            <p className="text-sm text-gray-500">Da Indicizzare</p>
          </div>
        </div>

        {lastSyncTime && (
          <div className="text-sm text-gray-500 text-center">
            Ultima sincronizzazione: {new Date(lastSyncTime).toLocaleString()}
          </div>
        )}
      </div>

      {/* Materials List */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Materiali del Corso</h4>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {materials.map((material) => {
            const currentOperation = syncOperations.find(op => op.materialId === material.id)
            const isCurrentlySyncing = currentOperation && currentOperation.status === 'running'

            return (
              <div
                key={material.id}
                className={`p-4 rounded-xl border transition-all duration-200 ${
                  currentOperation ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${getStatusColor(currentOperation?.status || 'pending')}`}>
                      {currentOperation ? getSyncStatusIcon(currentOperation.status) : <FileText className="h-4 w-4" />}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{material.name}</div>
                      <div className="text-sm text-gray-500">
                        {material.type} • {(material.size / 1024 / 1024).toFixed(1)} MB
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {material.indexingStatus && (
                      <span className={`badge text-xs ${getStatusColor(material.indexingStatus.status)}`}>
                        {material.indexingStatus.status === 'completed' ? 'Indicizzato' :
                         material.indexingStatus.status === 'processing' ? 'In corso' :
                         material.indexingStatus.status === 'failed' ? 'Fallito' : 'In attesa'}
                      </span>
                    )}
                    <button
                      onClick={() => manualSync(material.id)}
                      disabled={isCurrentlySyncing || isIndexing}
                      className="btn btn-primary btn-sm"
                    >
                      {isCurrentlySyncing ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <ArrowUpDown className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Progress Bar */}
                {currentOperation && currentOperation.status === 'running' && (
                  <div className="mt-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-600">Sincronizzazione in corso...</span>
                      <span className="text-xs text-gray-600">{currentOperation.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${currentOperation.progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {currentOperation && currentOperation.status === 'failed' && (
                  <div className="mt-3 p-2 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center space-x-2 text-sm text-red-700">
                      <AlertCircle className="h-4 w-4" />
                      <span>{currentOperation.errorMessage}</span>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )

  const renderAutoSync = () => (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-6">
          <h4 className="font-semibold text-gray-900">Sincronizzazione Automatica</h4>
          <button
            onClick={() => setAutoSyncConfig(prev => ({ ...prev, enabled: !prev.enabled }))}
            className={`btn ${autoSyncConfig.enabled ? 'btn-primary' : 'btn-secondary'}`}
          >
            {autoSyncConfig.enabled ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                Disattiva
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Attiva
              </>
            )}
          </button>
        </div>

        {autoSyncConfig.enabled && (
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
              <div className="flex items-center space-x-2 text-blue-800 mb-2">
                <Activity className="h-5 w-5" />
                <span className="font-medium">Auto-sync attivo</span>
              </div>
              <p className="text-sm text-blue-700">
                I materiali verranno sincronizzati automaticamente ogni {autoSyncConfig.interval} minuti
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Intervallo (minuti)
                </label>
                <input
                  type="number"
                  min="5"
                  max="1440"
                  value={autoSyncConfig.interval}
                  onChange={(e) => setAutoSyncConfig(prev => ({ ...prev, interval: parseInt(e.target.value) || 30 }))}
                  className="form-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dimensione Batch
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={autoSyncConfig.batchSize}
                  onChange={(e) => setAutoSyncConfig(prev => ({ ...prev, batchSize: parseInt(e.target.value) || 3 }))}
                  className="form-input"
                />
              </div>
            </div>

            <div className="space-y-3">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSyncConfig.onlyUnindexed}
                  onChange={(e) => setAutoSyncConfig(prev => ({ ...prev, onlyUnindexed: e.target.checked }))}
                  className="form-checkbox"
                />
                <span className="text-sm text-gray-700">Sincronizza solo materiali non indicizzati</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSyncConfig.retryFailed}
                  onChange={(e) => setAutoSyncConfig(prev => ({ ...prev, retryFailed: e.target.checked }))}
                  className="form-checkbox"
                />
                <span className="text-sm text-gray-700">Riprova automaticamente i sync falliti</span>
              </label>
            </div>
          </div>
        )}

        {!autoSyncConfig.enabled && (
          <div className="text-center py-8">
            <Cloud className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">La sincronizzazione automatica è disattivata</p>
          </div>
        )}
      </div>

      {/* Auto-sync History */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Cronologia Auto-sync</h4>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {syncOperations.filter(op => op.type === 'reindex').slice(-10).reverse().map((operation) => (
            <div key={operation.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getSyncStatusIcon(operation.status)}
                <div>
                  <div className="font-medium text-gray-900">{operation.materialName}</div>
                  <div className="text-xs text-gray-500">
                    {operation.startedAt && new Date(operation.startedAt).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className={`badge text-xs ${getStatusColor(operation.status)}`}>
                  {operation.status === 'completed' ? 'Completato' :
                   operation.status === 'running' ? 'In corso' :
                   operation.status === 'failed' ? 'Fallito' : 'In attesa'}
                </div>
                {operation.progress > 0 && operation.progress < 100 && (
                  <div className="text-xs text-gray-500 mt-1">{operation.progress}%</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderSchedule = () => (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Programmazione Sincronizzazioni</h4>

        <div className="space-y-4">
          <div className="p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center space-x-3 mb-3">
              <Database className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-gray-900">Stato Archivio</span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Materiali totali:</span>
                <span className="ml-2 font-medium">{materials.length}</span>
              </div>
              <div>
                <span className="text-gray-500">Indicizzati:</span>
                <span className="ml-2 font-medium text-green-600">
                  {materials.filter(m => m.indexingStatus?.status === 'completed').length}
                </span>
              </div>
              <div>
                <span className="text-gray-500">In corso:</span>
                <span className="ml-2 font-medium text-blue-600">
                  {syncOperations.filter(op => op.status === 'running').length}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Falliti:</span>
                <span className="ml-2 font-medium text-red-600">
                  {syncOperations.filter(op => op.status === 'failed').length}
                </span>
              </div>
            </div>
          </div>

          <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
            <div className="flex items-center space-x-2 text-yellow-800 mb-2">
              <Zap className="h-5 w-5" />
              <span className="font-medium">Ottimizzazione Performance</span>
            </div>
            <p className="text-sm text-yellow-700">
              Per evitare sovraccarichi, le sincronizzazioni vengono processate in batch
              con un limite massimo di {autoSyncConfig.batchSize} operazioni simultanee.
            </p>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <h4 className="font-semibold text-gray-900 mb-4">Stato Sistema</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-900">Servizio di indicizzazione</span>
            </div>
            <span className="text-green-600">Attivo</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Brain className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-900">Motore AI</span>
            </div>
            <span className="text-blue-600">Operativo</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-gray-600" />
              <span className="font-medium text-gray-900">Queue di sincronizzazione</span>
            </div>
            <span className="text-gray-600">
              {syncOperations.filter(op => op.status === 'pending' || op.status === 'running').length} in coda
            </span>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl">
              <ArrowUpDown className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Gestore Sincronizzazione Contenuti
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Mantieni i materiali sempre aggiornati e indicizzati
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm ${
              autoSyncConfig.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
            }`}>
              <Activity className="h-4 w-4" />
              <span>{autoSyncConfig.enabled ? 'Auto-sync attivo' : 'Manuale'}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {[
            { id: 'manual', label: 'Sincronizzazione', icon: RefreshCw },
            { id: 'auto', label: 'Automatica', icon: Settings },
            { id: 'schedule', label: 'Stato Sistema', icon: Database }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Based on Active Tab */}
      {activeTab === 'manual' && renderManualSync()}
      {activeTab === 'auto' && renderAutoSync()}
      {activeTab === 'schedule' && renderSchedule()}

      {/* Global Loading Indicator */}
      {isAutoSyncing && (
        <div className="glass rounded-2xl p-4 border border-blue-200 bg-blue-50">
          <div className="flex items-center space-x-3">
            <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
            <span className="text-blue-800">Sincronizzazione automatica in corso...</span>
          </div>
        </div>
      )}
    </div>
  )
}