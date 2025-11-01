import { useState, useEffect, useCallback } from 'react'
import { MaterialIndexingStatus, ContentAnalysisResult, Concept, TestQuestion } from '@/types/indexing'

interface UseContentIndexingReturn {
  indexingStatus: MaterialIndexingStatus | null
  analysisResult: ContentAnalysisResult | null
  isIndexing: boolean
  startIndexing: (materialId: string) => Promise<void>
  checkIndexingStatus: (materialId: string) => Promise<void>
  retryIndexing: (materialId: string) => Promise<void>
  clearIndexingStatus: () => void
}

export function useContentIndexing(): UseContentIndexingReturn {
  const [indexingStatus, setIndexingStatus] = useState<MaterialIndexingStatus | null>(null)
  const [analysisResult, setAnalysisResult] = useState<ContentAnalysisResult | null>(null)
  const [isIndexing, setIsIndexing] = useState(false)

  const checkIndexingStatus = useCallback(async (materialId: string) => {
    try {
      const response = await fetch(`/api/materials/${materialId}/indexing-status`)
      if (response.ok) {
        const data = await response.json()
        setIndexingStatus(data)
        setIsIndexing(data.status === 'processing')

        if (data.status === 'completed') {
          // Fetch analysis result when indexing completes
          const analysisResponse = await fetch(`/api/materials/${materialId}/analysis`)
          if (analysisResponse.ok) {
            const analysisData = await analysisResponse.json()
            setAnalysisResult(analysisData)
          }
        }
      }
    } catch (error) {
      console.error('Error checking indexing status:', error)
    }
  }, [])

  const startIndexing = useCallback(async (materialId: string) => {
    try {
      setIsIndexing(true)
      setIndexingStatus({
        material_id: materialId,
        status: 'processing',
        total_chunks: 0,
        processed_chunks: 0,
        extracted_concepts: 0,
        generated_questions: 0,
        processing_started_at: new Date().toISOString()
      })

      const response = await fetch(`/api/materials/${materialId}/index`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to start indexing')
      }

      // Start polling for status updates
      const pollInterval = setInterval(() => {
        checkIndexingStatus(materialId)
      }, 2000)

      // Poll until completion or error
      setTimeout(() => {
        clearInterval(pollInterval)
        checkIndexingStatus(materialId)
      }, 60000) // Stop polling after 1 minute

    } catch (error) {
      console.error('Error starting indexing:', error)
      setIsIndexing(false)
      setIndexingStatus(null)
    }
  }, [checkIndexingStatus])

  const retryIndexing = useCallback(async (materialId: string) => {
    try {
      setIsIndexing(true)
      setIndexingStatus({
        material_id: materialId,
        status: 'processing',
        total_chunks: 0,
        processed_chunks: 0,
        extracted_concepts: 0,
        generated_questions: 0,
        processing_started_at: new Date().toISOString()
      })

      const response = await fetch(`/api/materials/${materialId}/reindex`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to start reindexing')
      }

      // Start polling for status updates
      const pollInterval = setInterval(() => {
        checkIndexingStatus(materialId)
      }, 2000)

      setTimeout(() => {
        clearInterval(pollInterval)
        checkIndexingStatus(materialId)
      }, 60000)

    } catch (error) {
      console.error('Error starting reindexing:', error)
      setIsIndexing(false)
      setIndexingStatus(null)
    }
  }, [checkIndexingStatus])

  const clearIndexingStatus = useCallback(() => {
    setIndexingStatus(null)
    setAnalysisResult(null)
    setIsIndexing(false)
  }, [])

  return {
    indexingStatus,
    analysisResult,
    isIndexing,
    startIndexing,
    checkIndexingStatus,
    retryIndexing,
    clearIndexingStatus
  }
}

// Hook for managing concept knowledge and test generation
interface UseConceptKnowledgeReturn {
  concepts: Concept[]
  testQuestions: TestQuestion[]
  isLoading: boolean
  error: string | null
  fetchConcepts: (courseId: string) => Promise<void>
  generateTestQuestions: (conceptIds: string[], count: number, difficulty?: number) => Promise<void>
  updateConceptMastery: (conceptId: string, masteryLevel: number) => Promise<void>
  getStudyRecommendations: (courseId: string) => Promise<any[]>
}

export function useConceptKnowledge(): UseConceptKnowledgeReturn {
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [testQuestions, setTestQuestions] = useState<TestQuestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchConcepts = useCallback(async (courseId: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch(`/api/courses/${courseId}/concepts`)
      if (!response.ok) {
        throw new Error('Failed to fetch concepts')
      }

      const data = await response.json()
      setConcepts(data.concepts || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch concepts')
      console.error('Error fetching concepts:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const generateTestQuestions = useCallback(async (
    conceptIds: string[],
    count: number,
    difficulty?: number
  ) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch('/api/test-questions/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          concept_ids: conceptIds,
          count,
          difficulty
        })
      })

      if (!response.ok) {
        throw new Error('Failed to generate test questions')
      }

      const data = await response.json()
      setTestQuestions(data.questions || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate test questions')
      console.error('Error generating test questions:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const updateConceptMastery = useCallback(async (conceptId: string, masteryLevel: number) => {
    try {
      const response = await fetch(`/api/concepts/${conceptId}/mastery`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mastery_level: masteryLevel
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update concept mastery')
      }

      // Update local state
      setConcepts(prev =>
        prev.map(concept =>
          concept.id === conceptId
            ? { ...concept, mastery_level: masteryLevel }
            : concept
        )
      )
    } catch (err) {
      console.error('Error updating concept mastery:', err)
      throw err
    }
  }, [])

  const getStudyRecommendations = useCallback(async (courseId: string) => {
    try {
      const response = await fetch(`/api/courses/${courseId}/recommendations`)
      if (!response.ok) {
        throw new Error('Failed to fetch study recommendations')
      }

      return await response.json()
    } catch (err) {
      console.error('Error fetching study recommendations:', err)
      throw err
    }
  }, [])

  return {
    concepts,
    testQuestions,
    isLoading,
    error,
    fetchConcepts,
    generateTestQuestions,
    updateConceptMastery,
    getStudyRecommendations
  }
}