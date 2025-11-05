'use client'

import { useState, useEffect } from 'react'
import { Clock, CheckCircle, AlertCircle, XCircle, RefreshCw, X } from 'lucide-react'

interface Task {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  message: string
  result?: unknown
  error?: string
  created_at: string
  started_at?: string
  completed_at?: string
  course_id: string
  task_type: string
}

interface BackgroundTaskProgressProps {
  taskId: string
  onComplete?: (result: unknown) => void
  onError?: (error: string) => void
  onCancel?: () => void
  showCancelButton?: boolean
}

export default function BackgroundTaskProgress({
  taskId,
  onComplete,
  onError,
  onCancel,
  showCancelButton = true
}: BackgroundTaskProgressProps) {
  const [task, setTask] = useState<Task | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!taskId) return

    const fetchTaskStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/tasks/${taskId}`)
        if (response.ok) {
          const taskData: Task = await response.json()
          setTask(taskData)
          setError(null)

          // Handle completion
          if (taskData.status === 'completed' && typeof taskData.result !== 'undefined') {
            onComplete?.(taskData.result)
          } else if (taskData.status === 'failed' && taskData.error) {
            onError?.(taskData.error)
          }
        } else {
          setError('Impossibile caricare lo stato del task')
        }
      } catch {
        setError('Errore di connessione')
      } finally {
        setIsLoading(false)
      }
    }

    // Initial fetch
    fetchTaskStatus()

    // Set up polling for running tasks
    let intervalId: ReturnType<typeof setInterval>
    if (taskId) {
      intervalId = setInterval(fetchTaskStatus, 2000) // Poll every 2 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [taskId, onComplete, onError])

  const handleCancel = async () => {
    if (!taskId) return

    try {
      const response = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        onCancel?.()
      } else {
        setError('Impossibile cancellare il task')
      }
    } catch {
      setError('Errore durante la cancellazione')
    }
  }

  if (isLoading) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
          <span className="text-blue-800">Caricamento stato task...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-gray-600" />
          <span className="text-gray-800">Task non trovato</span>
        </div>
      </div>
    )
  }

  const getStatusIcon = () => {
    switch (task.status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-600" />
      case 'running':
        return <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusColor = () => {
    switch (task.status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-200'
      case 'running':
        return 'bg-blue-50 border-blue-200'
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'failed':
        return 'bg-red-50 border-red-200'
      case 'cancelled':
        return 'bg-gray-50 border-gray-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getStatusTextColor = () => {
    switch (task.status) {
      case 'pending':
        return 'text-yellow-800'
      case 'running':
        return 'text-blue-800'
      case 'completed':
        return 'text-green-800'
      case 'failed':
        return 'text-red-800'
      case 'cancelled':
        return 'text-gray-800'
      default:
        return 'text-gray-800'
    }
  }

  const getProgressColor = () => {
    switch (task.status) {
      case 'pending':
        return 'bg-yellow-500'
      case 'running':
        return 'bg-blue-500'
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'cancelled':
        return 'bg-gray-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className={`${getStatusColor()} border rounded-lg p-4 relative`}>
      {/* Cancel button for running tasks */}
      {showCancelButton && task.status === 'running' && (
        <button
          onClick={handleCancel}
          className="absolute top-2 right-2 p-1 hover:bg-white/50 rounded-full transition-colors"
          title="Cancella task"
        >
          <X className="h-4 w-4 text-gray-600" />
        </button>
      )}

      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className={`font-medium ${getStatusTextColor()}`}>
                {task.status === 'pending' && 'In attesa'}
                {task.status === 'running' && 'In elaborazione'}
                {task.status === 'completed' && 'Completato'}
                {task.status === 'failed' && 'Fallito'}
                {task.status === 'cancelled' && 'Cancellato'}
              </span>
              <span className="text-sm text-gray-500">
                {task.progress.toFixed(0)}%
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{task.message}</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`${getProgressColor()} h-2 rounded-full transition-all duration-300 ease-out`}
            style={{ width: `${task.progress}%` }}
          />
        </div>

        {/* Task details */}
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>ID Task: {task.id.slice(0, 8)}...</span>
            <span>{new Date(task.created_at).toLocaleTimeString()}</span>
          </div>
          {task.started_at && (
            <div>Iniziato: {new Date(task.started_at).toLocaleTimeString()}</div>
          )}
          {task.completed_at && (
            <div>Completato: {new Date(task.completed_at).toLocaleTimeString()}</div>
          )}
        </div>

        {/* Error message */}
        {task.status === 'failed' && task.error && (
          <div className="bg-red-100 border border-red-200 rounded p-2 text-sm text-red-800">
            <strong>Errore:</strong> {task.error}
          </div>
        )}

        {/* Success result preview */}
        {task.status === 'completed' && task.result && (() => {
          const result = task.result as {
            sessions_count?: number
            estimated_hours?: number
            chapters_detected?: number
            topics_extracted?: number
          }

          if (!result.sessions_count) {
            return null
          }

          return (
          <div className="bg-green-100 border border-green-200 rounded p-3 text-sm">
            <div className="font-medium text-green-800 mb-2">Risultato:</div>
            <div className="text-green-700">
              • {result.sessions_count} sessioni generate<br/>
              • {result.estimated_hours ?? 0} ore totali<br/>
              • {result.chapters_detected ?? 0} capitoli rilevati<br/>
              • {result.topics_extracted ?? 0} argomenti estratti
            </div>
          </div>
          )
        })()}
      </div>
    </div>
  )
}

// Hook for managing background tasks
export function useBackgroundTask(taskId: string | null) {
  const [task, setTask] = useState<Task | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!taskId) {
      setTask(null)
      setError(null)
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    let intervalId: ReturnType<typeof setInterval>

    const fetchTaskStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/tasks/${taskId}`)
        if (response.ok) {
          const taskData: Task = await response.json()
          setTask(taskData)
          setError(null)

          // Stop polling if task is completed/failed/cancelled
          if (['completed', 'failed', 'cancelled'].includes(taskData.status)) {
            clearInterval(intervalId)
          }
        } else {
          setError('Impossibile caricare lo stato del task')
        }
      } catch {
        setError('Errore di connessione')
      } finally {
        setIsLoading(false)
      }
    }

    fetchTaskStatus()
    intervalId = setInterval(fetchTaskStatus, 2000)

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [taskId])

  const cancelTask = async () => {
    if (!taskId) return false

    try {
      const response = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: 'DELETE'
      })
      return response.ok
    } catch {
      return false
    }
  }

  return {
    task,
    isLoading,
    error,
    cancelTask
  }
}
