import { useState, useEffect, useCallback, useRef } from 'react'

// Temporary interface definition
interface PDFAnnotation {
  id: string
  user_id: string
  pdf_filename: string
  pdf_path: string
  course_id: string
  book_id: string
  page_number: number
  type: 'highlight' | 'underline' | 'note' | 'strikeout' | 'text'
  text: string
  selected_text: string
  content: string
  position: {
    x: number
    y: number
    width: number
    height: number
  }
  style: {
    color: string
    opacity: number
    stroke_color: string
    stroke_width: number
  }
  tags: string[]
  is_public: boolean
  is_favorite: boolean
  created_at: string
  updated_at: string
}

interface UseAnnotationsSyncProps {
  userId: string
  pdfFilename: string
  pdfUrl: string
  courseId?: string
  bookId?: string
  autoSync?: boolean
  syncInterval?: number
}

interface SyncStatus {
  isOnline: boolean
  lastSync: Date | null
  isSyncing: boolean
  pendingChanges: number
  syncErrors: string[]
}

export function useAnnotationsSync({
  userId,
  pdfFilename,
  pdfUrl,
  courseId = "",
  bookId = "",
  autoSync = true,
  syncInterval = 30000 // 30 seconds
}: UseAnnotationsSyncProps) {
  const [annotations, setAnnotations] = useState<PDFAnnotation[]>([])
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isOnline: navigator.onLine,
    lastSync: null,
    isSyncing: false,
    pendingChanges: 0,
    syncErrors: []
  })

  const syncTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingOperationsRef = useRef<Array<{
    type: 'create' | 'update' | 'delete'
    annotation?: PDFAnnotation
    annotationId?: string
    timestamp: number
  }>>([])

  // API helper function
  const apiCall = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('API call failed:', error)
      throw error
    }
  }, [])

  // Load annotations from server
  const loadAnnotations = useCallback(async () => {
    try {
      setSyncStatus(prev => ({ ...prev, isSyncing: true, syncErrors: [] }))

      const response = await apiCall(
        `/annotations/${userId}/${encodeURIComponent(pdfFilename)}?course_id=${courseId}&book_id=${bookId}`
      )

      if (response.annotations) {
        setAnnotations(response.annotations)
        setSyncStatus(prev => ({
          ...prev,
          lastSync: new Date(),
          isSyncing: false,
          pendingChanges: pendingOperationsRef.current.length
        }))
      }

      return response.annotations
    } catch (error) {
      console.error('Failed to load annotations:', error)

      // Fallback to localStorage
      try {
        const localAnnotations = localStorage.getItem(`pdf-annotations-${pdfFilename}`)
        if (localAnnotations) {
          const parsed = JSON.parse(localAnnotations)
          setAnnotations(parsed)
        }
      } catch (parseError) {
        console.error('Error parsing local annotations:', parseError)
      }

      setSyncStatus(prev => ({
        ...prev,
        isSyncing: false,
        syncErrors: [...prev.syncErrors, `Failed to load: ${error instanceof Error ? error.message : 'Unknown error'}`]
      }))

      return []
    }
  }, [apiCall, userId, pdfFilename, courseId, bookId])

  // Save annotation to server
  const saveAnnotation = useCallback(async (annotation: PDFAnnotation) => {
    try {
      // Optimistically update local state
      setAnnotations(prev => [...prev, annotation])

      // Add to pending operations
      pendingOperationsRef.current.push({
        type: 'create',
        annotation,
        timestamp: Date.now()
      })

      setSyncStatus(prev => ({
        ...prev,
        pendingChanges: pendingOperationsRef.current.length
      }))

      // Try to save to server
      const response = await apiCall('/annotations', {
        method: 'POST',
        body: JSON.stringify(annotation),
      })

      if (response.success) {
        // Remove from pending operations
        pendingOperationsRef.current = pendingOperationsRef.current.filter(
          op => !(op.type === 'create' && op.annotation?.id === annotation.id)
        )

        // Update with server response (includes server-generated ID)
        if (response.annotation && response.annotation.id !== annotation.id) {
          setAnnotations(prev => prev.map(ann =>
            ann.id === annotation.id ? response.annotation : ann
          ))
        }

        setSyncStatus(prev => ({
          ...prev,
          lastSync: new Date(),
          pendingChanges: pendingOperationsRef.current.length
        }))

        return response.annotation
      } else {
        throw new Error('Server response indicated failure')
      }
    } catch (error) {
      console.error('Failed to save annotation:', error)

      // Save to localStorage as fallback
      const localAnnotations = [...annotations, annotation]
      localStorage.setItem(`pdf-annotations-${pdfFilename}`, JSON.stringify(localAnnotations))

      setSyncStatus(prev => ({
        ...prev,
        syncErrors: [...prev.syncErrors, `Failed to save annotation: ${error instanceof Error ? error.message : 'Unknown error'}`]
      }))

      return annotation
    }
  }, [apiCall, annotations, pdfFilename])

  // Update annotation on server
  const updateAnnotation = useCallback(async (annotationId: string, updates: Partial<PDFAnnotation>) => {
    try {
      // Optimistically update local state
      setAnnotations(prev => prev.map(ann =>
        ann.id === annotationId ? { ...ann, ...updates, updated_at: new Date().toISOString() } : ann
      ))

      // Add to pending operations
      pendingOperationsRef.current.push({
        type: 'update',
        annotationId,
        timestamp: Date.now()
      })

      setSyncStatus(prev => ({
        ...prev,
        pendingChanges: pendingOperationsRef.current.length
      }))

      const response = await apiCall(`/annotations/${userId}/${annotationId}?pdf_filename=${encodeURIComponent(pdfFilename)}&course_id=${courseId}&book_id=${bookId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      })

      if (response.success) {
        // Remove from pending operations
        pendingOperationsRef.current = pendingOperationsRef.current.filter(
          op => !(op.type === 'update' && op.annotationId === annotationId)
        )

        setSyncStatus(prev => ({
          ...prev,
          lastSync: new Date(),
          pendingChanges: pendingOperationsRef.current.length
        }))

        return response.annotation
      } else {
        throw new Error('Server response indicated failure')
      }
    } catch (error) {
      console.error('Failed to update annotation:', error)

      // Update localStorage as fallback
      const localAnnotations = annotations.map(ann =>
        ann.id === annotationId ? { ...ann, ...updates, updated_at: new Date().toISOString() } : ann
      )
      localStorage.setItem(`pdf-annotations-${pdfFilename}`, JSON.stringify(localAnnotations))

      setSyncStatus(prev => ({
        ...prev,
        syncErrors: [...prev.syncErrors, `Failed to update annotation: ${error instanceof Error ? error.message : 'Unknown error'}`]
      }))

      return null
    }
  }, [apiCall, userId, annotations, pdfFilename, courseId, bookId])

  // Delete annotation from server
  const deleteAnnotation = useCallback(async (annotationId: string) => {
    try {
      // Optimistically update local state
      setAnnotations(prev => prev.filter(ann => ann.id !== annotationId))

      // Add to pending operations
      pendingOperationsRef.current.push({
        type: 'delete',
        annotationId,
        timestamp: Date.now()
      })

      setSyncStatus(prev => ({
        ...prev,
        pendingChanges: pendingOperationsRef.current.length
      }))

      await apiCall(`/annotations/${userId}/${annotationId}?pdf_filename=${encodeURIComponent(pdfFilename)}&course_id=${courseId}&book_id=${bookId}`, {
        method: 'DELETE',
      })

      // Remove from pending operations
      pendingOperationsRef.current = pendingOperationsRef.current.filter(
        op => !(op.type === 'delete' && op.annotationId === annotationId)
      )

      setSyncStatus(prev => ({
        ...prev,
        lastSync: new Date(),
        pendingChanges: pendingOperationsRef.current.length
      }))

      return true
    } catch (error) {
      console.error('Failed to delete annotation:', error)

      // Restore from localStorage if available
      try {
        const localAnnotations = localStorage.getItem(`pdf-annotations-${pdfFilename}`)
        if (localAnnotations) {
          const parsed = JSON.parse(localAnnotations)
          const deletedAnnotation = parsed.find((ann: PDFAnnotation) => ann.id === annotationId)
          if (deletedAnnotation) {
            setAnnotations(prev => [...prev, deletedAnnotation])
          }
        }
      } catch (parseError) {
        console.error('Error restoring annotation from localStorage:', parseError)
      }

      setSyncStatus(prev => ({
        ...prev,
        syncErrors: [...prev.syncErrors, `Failed to delete annotation: ${error instanceof Error ? error.message : 'Unknown error'}`]
      }))

      return false
    }
  }, [apiCall, userId, pdfFilename, courseId, bookId])

  // Sync pending operations
  const syncPendingOperations = useCallback(async () => {
    if (!syncStatus.isOnline || syncStatus.isSyncing || pendingOperationsRef.current.length === 0) {
      return
    }

    setSyncStatus(prev => ({ ...prev, isSyncing: true }))

    const operations = [...pendingOperationsRef.current]
    const errors: string[] = []

    for (const operation of operations) {
      try {
        if (operation.type === 'create' && operation.annotation) {
          await saveAnnotation(operation.annotation)
        } else if (operation.type === 'update' && operation.annotationId) {
          const annotation = annotations.find(ann => ann.id === operation.annotationId)
          if (annotation) {
            await apiCall(`/annotations/${userId}/${operation.annotationId}?pdf_filename=${encodeURIComponent(pdfFilename)}&course_id=${courseId}&book_id=${bookId}`, {
              method: 'PUT',
              body: JSON.stringify(annotation),
            })
          }
        } else if (operation.type === 'delete' && operation.annotationId) {
          await apiCall(`/annotations/${userId}/${operation.annotationId}?pdf_filename=${encodeURIComponent(pdfFilename)}&course_id=${courseId}&book_id=${bookId}`, {
            method: 'DELETE',
          })
        }

        // Remove successful operation
        pendingOperationsRef.current = pendingOperationsRef.current.filter(
          op => op !== operation
        )
      } catch (error) {
        errors.push(`Failed to sync ${operation.type}: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    }

    setSyncStatus(prev => ({
      ...prev,
      isSyncing: false,
      lastSync: new Date(),
      pendingChanges: pendingOperationsRef.current.length,
      syncErrors: errors.length > 0 ? errors : prev.syncErrors
    }))
  }, [syncStatus.isOnline, syncStatus.isSyncing, annotations, apiCall, userId, pdfFilename, courseId, bookId])

  // Manual sync
  const manualSync = useCallback(async () => {
    await loadAnnotations()
    await syncPendingOperations()
  }, [loadAnnotations, syncPendingOperations])

  // Export annotations
  const exportAnnotations = useCallback(async (format: 'json' | 'markdown' | 'csv' = 'json') => {
    try {
      const response = await apiCall(`/annotations/${userId}/export?format=${format}&course_id=${courseId}&book_id=${bookId}`)

      if (response.success) {
        return response.data
      } else {
        throw new Error('Export failed')
      }
    } catch (error) {
      console.error('Failed to export annotations:', error)

      // Fallback to local export
      const exportData = {
        user_id: userId,
        pdf_filename: pdfFilename,
        export_date: new Date().toISOString(),
        total_annotations: annotations.length,
        annotations: annotations
      }

      return exportData
    }
  }, [apiCall, userId, pdfFilename, courseId, bookId, annotations])

  // Import annotations
  const importAnnotations = useCallback(async (importData: unknown, format: 'json' | 'markdown' = 'json') => {
    try {
      const response = await apiCall(`/annotations/${userId}/import`, {
        method: 'POST',
        body: JSON.stringify({
          annotations_data: importData,
          format
        }),
      })

      if (response.success) {
        await loadAnnotations() // Reload annotations
        return response.imported_count
      } else {
        throw new Error('Import failed')
      }
    } catch (error) {
      console.error('Failed to import annotations:', error)
      return 0
    }
  }, [apiCall, userId, pdfFilename, pdfUrl, courseId, bookId, annotations])

  // Clear sync errors
  const clearSyncErrors = useCallback(() => {
    setSyncStatus(prev => ({ ...prev, syncErrors: [] }))
  }, [])

  // Effects
  useEffect(() => {
    // Load annotations on mount
    loadAnnotations()

    // Set up online/offline listeners
    const handleOnline = () => {
      setSyncStatus(prev => ({ ...prev, isOnline: true }))
      // Try to sync pending operations when coming back online
      if (pendingOperationsRef.current.length > 0) {
        syncPendingOperations()
      }
    }

    const handleOffline = () => {
      setSyncStatus(prev => ({ ...prev, isOnline: false }))
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [loadAnnotations, syncPendingOperations])

  // Auto-sync interval
  useEffect(() => {
    if (autoSync && syncStatus.isOnline) {
      syncTimeoutRef.current = setInterval(() => {
        if (pendingOperationsRef.current.length > 0) {
          syncPendingOperations()
        }
      }, syncInterval)

      return () => {
        if (syncTimeoutRef.current) {
          clearInterval(syncTimeoutRef.current)
        }
      }
    }
  }, [autoSync, syncStatus.isOnline, syncInterval, syncPendingOperations])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (syncTimeoutRef.current) {
        clearInterval(syncTimeoutRef.current)
      }
    }
  }, [])

  return {
    // Data
    annotations,
    syncStatus,

    // Actions
    loadAnnotations,
    saveAnnotation,
    updateAnnotation,
    deleteAnnotation,
    manualSync,
    exportAnnotations,
    importAnnotations,
    clearSyncErrors,

    // Computed values
    hasPendingChanges: syncStatus.pendingChanges > 0,
    isHealthy: syncStatus.isOnline && syncStatus.syncErrors.length === 0
  }
}
