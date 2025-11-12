/**
 * CLE API Client v1
 * Standardized API client for all Cognitive Learning Engine endpoints
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

// Base configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
// const API_VERSION = 'v1' // Disabled - backend doesn't use versioning

// Types
interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  detail?: string
  timestamp: string
}

interface ApiError {
  success: false
  error: string
  detail: string
  timestamp: string
}

// Authentication
interface AuthTokens {
  access_token: string
  token_type: string
  expires_in: number
}

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL: `${baseURL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    })

    // Request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken()
          // Redirect to login or handle auth error
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Authentication methods
  setToken(token: string) {
    this.token = token
    localStorage.setItem('cle_access_token', token)
  }

  getToken(): string | null {
    if (this.token) return this.token
    if (typeof window !== 'undefined') {
      return localStorage.getItem('cle_access_token')
    }
    return null
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('cle_access_token')
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken()
  }

  // Generic request methods
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    let attempt = 0
    const maxAttempts = 4
    let lastError: any = null
    while (attempt < maxAttempts) {
      try {
        const response: AxiosResponse = await this.client.request(config)
        return {
          success: true,
          data: response.data,
          timestamp: new Date().toISOString()
        }
      } catch (error: any) {
        lastError = error
        const status = error?.response?.status
        if (status === 429) {
          const retryAfterHeader = error?.response?.headers?.['retry-after']
          const retryAfterBody = error?.response?.data?.retry_after
          const retrySeconds = Number.isFinite(parseInt(retryAfterHeader)) ? parseInt(retryAfterHeader) : (Number.isFinite(retryAfterBody) ? retryAfterBody : 1)
          const delayMs = Math.min(8000, Math.max(500, (2 ** attempt) * 500, retrySeconds * 1000))
          await new Promise((r) => setTimeout(r, delayMs))
          attempt += 1
          continue
        }
        break
      }
    }
    const apiError: ApiError = lastError?.response?.data || {
      success: false,
      error: 'Unknown Error',
      detail: lastError?.message,
      timestamp: new Date().toISOString()
    }
    return {
      ...apiError,
      success: false
    }
  }

  async get<T>(url: string, params?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'GET', url, params })
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'POST', url, data })
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'PUT', url, data })
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'DELETE', url })
  }
}

// Create default client instance
const apiClient = new ApiClient()

// Utility functions
const handleApiResponse = <T>(response: ApiResponse<T>) => {
  if (response.success) {
    return {
      data: response.data,
      error: null
    }
  } else {
    return {
      data: null,
      error: response.error || response.detail || 'Unknown error'
    }
  }
}

const formatDateForBackend = (date: Date): string => {
  return date.toISOString()
}

const parseDateFromBackend = (dateString: string): Date => {
  return new Date(dateString)
}

// Health check
const healthCheck = async () => {
  const response = await apiClient.get('/health')
  return handleApiResponse(response)
}

// =================== SPACED REPETITION ===================

export interface LearningCard {
  id: string
  course_id: string
  question: string
  answer: string
  card_type: string
  difficulty: number
  ease_factor: number
  interval_days: number
  repetitions: number
  next_review: string
  created_at: string
  last_reviewed?: string
  review_count: number
  total_quality: number
  context_tags: string[]
  source_material?: string
}

export interface CreateCardRequest {
  course_id: string
  question: string
  answer: string
  card_type?: string
  concept_id?: string
  context_tags?: string[]
  source_material?: string
}

export interface CardReviewRequest {
  card_id: string
  quality_rating: number
  response_time_ms: number
  session_id?: string
}

export interface StudySession {
  session_id: string
  user_id: string
  course_id: string
  cards: LearningCard[]
  total_cards: number
  session_type: string
  started_at: string
}

// Spaced Repetition API calls
export const spacedRepetitionApi = {
  // Cards
  createCard: async (data: CreateCardRequest) => {
    const response = await apiClient.post('/spaced-repetition/cards', data)
    return handleApiResponse<LearningCard>(response as ApiResponse<LearningCard>)
  },

  getDueCards: async (courseId: string, userId: string, limit = 20) => {
    const response = await apiClient.get(`/spaced-repetition/courses/${courseId}/cards/due`, {
      user_id: userId,
      limit
    })
    return handleApiResponse<LearningCard[]>(response as ApiResponse<LearningCard[]>)
  },

  reviewCard: async (data: CardReviewRequest) => {
    const response = await apiClient.post('/spaced-repetition/cards/review', data)
    return handleApiResponse(response)
  },

  // Sessions
  createSession: async (userId: string, courseId: string, sessionType = 'mixed', maxCards = 20) => {
    const response = await apiClient.post('/spaced-repetition/session', {
      user_id: userId,
      course_id: courseId,
      session_type: sessionType,
      max_cards: maxCards
    })
    return handleApiResponse<StudySession>(response as ApiResponse<StudySession>)
  },

  // Analytics
  getAnalytics: async (courseId: string, userId: string, periodDays = 30) => {
    const response = await apiClient.get('/spaced-repetition/analytics', {
      params: {
        user_id: userId,
        course_id: courseId,
        period_days: periodDays
      }
    })
    return handleApiResponse(response)
  }
}

// =================== ACTIVE RECALL ===================

export interface Question {
  id: string
  text: string
  type: string
  difficulty: string
  options?: string[]
  correct_answer: string
  explanation?: string
  bloom_level: string
}

export interface QuestionGenerationRequest {
  content: string
  num_questions?: number
  difficulty?: string
  question_types?: string[]
  bloom_levels?: string[]
}

export interface QuestionSubmission {
  question_id: string
  user_answer: string
  response_time_ms: number
  confidence_level?: number
}

// Active Recall API calls
export const activeRecallApi = {
  generateQuestions: async (data: QuestionGenerationRequest) => {
    const response = await apiClient.post('/active-recall/questions/generate', data)
    return handleApiResponse(response)
  },

  submitAnswer: async (data: QuestionSubmission) => {
    const response = await apiClient.post('/active-recall/questions/submit', data)
    return handleApiResponse(response)
  },

  startSession: async (userId: string, courseId: string, questionCount = 10) => {
    const response = await apiClient.post('/active-recall/sessions/start', {
      user_id: userId,
      course_id: courseId,
      question_count: questionCount
    })
    return handleApiResponse(response)
  },

  getNextQuestion: async (sessionId: string) => {
    const response = await apiClient.get(`/active-recall/sessions/${sessionId}/next-question`)
    return handleApiResponse<Question>(response as ApiResponse<Question>)
  },

  completeSession: async (sessionId: string, userId: string) => {
    const response = await apiClient.post(`/active-recall/sessions/${sessionId}/complete`, {
      user_id: userId
    })
    return handleApiResponse(response)
  }
}

// =================== DUAL CODING ===================

export interface DualCodingRequest {
  content: string
  content_type?: string
  target_audience?: string
  learning_style?: string
}

export interface VisualElement {
  id: string
  type: string
  title: string
  description: string
  data: any
}

// Dual Coding API calls
export const dualCodingApi = {
  createContent: async (data: DualCodingRequest) => {
    const response = await apiClient.post('/dual-coding/content/create', data)
    return handleApiResponse(response)
  },

  enhanceContent: async (contentId: string, enhancementType: string, targetLearningStyle = 'balanced') => {
    const response = await apiClient.post('/dual-coding/content/enhance', {
      content_id: contentId,
      enhancement_type: enhancementType,
      target_learning_style: targetLearningStyle
    })
    return handleApiResponse(response)
  },

  getVisualElements: async () => {
    const response = await apiClient.get('/dual-coding/visual-elements')
    return handleApiResponse<VisualElement[]>(response as ApiResponse<VisualElement[]>)
  }
}

// =================== INTERLEAVED PRACTICE ===================

export interface Concept {
  id: string
  name: string
  description: string
  difficulty: number
  mastery_level: number
}

export interface ScheduleRequest {
  user_id: string
  course_id: string
  concepts: Concept[]
  session_duration_minutes?: number
}

// Interleaved Practice API calls
export const interleavedPracticeApi = {
  createSchedule: async (data: ScheduleRequest) => {
    const response = await apiClient.post('/interleaved-practice/schedules', data)
    return handleApiResponse(response)
  },

  getPracticePatterns: async () => {
    const response = await apiClient.get('/interleaved-practice/patterns')
    return handleApiResponse(response)
  },

  submitFeedback: async (sessionId: string, feedback: any) => {
    const response = await apiClient.post(`/interleaved-practice/sessions/${sessionId}/feedback`, feedback)
    return handleApiResponse(response)
  }
}

// =================== METACOGNITION ===================

export interface MetacognitiveSession {
  session_id: string
  user_id: string
  course_id: string
  session_type: string
  phases: any[]
  activities: any[]
  created_at: string
}

export interface ReflectionActivity {
  activity_id: string
  user_id: string
  activity_type: string
  reflection_prompts: string[]
  duration_minutes: number
}

// Metacognition API calls
export const metacognitionApi = {
  createSession: async (userId: string, courseId: string, learningContext: any, sessionType = 'comprehensive') => {
    const response = await apiClient.post('/metacognition/sessions', {
      user_id: userId,
      course_id: courseId,
      learning_context: learningContext,
      session_type: sessionType
    })
    return handleApiResponse<MetacognitiveSession>(response as ApiResponse<MetacognitiveSession>)
  },

  createReflectionActivity: async (userId: string, courseId: string, activityType: string, reflectionContext: any) => {
    const response = await apiClient.post('/metacognition/reflection-activities', {
      user_id: userId,
      course_id: courseId,
      activity_type: activityType,
      reflection_context: reflectionContext
    })
    return handleApiResponse<ReflectionActivity>(response as ApiResponse<ReflectionActivity>)
  },

  getAnalytics: async (userId: string, courseId: string, periodDays = 30) => {
    const response = await apiClient.get('/metacognition/analytics', {
      params: {
        user_id: userId,
        course_id: courseId,
        period_days: periodDays
      }
    })
    return handleApiResponse(response)
  }
}

// =================== ELABORATION NETWORK ===================

export interface NetworkNode {
  id: string
  label: string
  type: string
  data: any
}

export interface NetworkEdge {
  id: string
  source: string
  target: string
  type: string
  weight: number
}

export interface NetworkVisualization {
  nodes: NetworkNode[]
  edges: NetworkEdge[]
  layout: string
}

// Elaboration Network API calls
export const elaborationNetworkApi = {
  buildNetwork: async (userId: string, courseId: string, knowledgeBase: any, learningObjectives: string[] = []) => {
    const response = await apiClient.post('/elaboration-network/build', {
      user_id: userId,
      course_id: courseId,
      knowledge_base: knowledgeBase,
      learning_objectives: learningObjectives
    })
    return handleApiResponse(response)
  },

  visualizeNetwork: async (networkId: string, config: any = {}) => {
    const response = await apiClient.post('/elaboration-network/visualize', {
      network_id: networkId,
      config
    })
    return handleApiResponse<NetworkVisualization>(response as ApiResponse<NetworkVisualization>)
  },

  getAnalytics: async (userId: string, courseId: string, periodDays = 30) => {
    const response = await apiClient.get('/elaboration-network/analytics', {
      params: {
        user_id: userId,
        course_id: courseId,
        period_days: periodDays
      }
    })
    return handleApiResponse(response)
  }
}

// Utility exports
export {
  apiClient,
  handleApiResponse,
  formatDateForBackend,
  parseDateFromBackend,
  healthCheck
}

export default apiClient
