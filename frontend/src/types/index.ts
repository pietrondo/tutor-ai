/**
 * Global TypeScript definitions for Tutor AI Frontend
 * Ensures type safety across the entire application
 */

// ===== USER TYPES (Local Setup - Simplified) =====

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system'
  language?: 'it' | 'en'
  study?: StudyPreferences
}

export interface StudyPreferences {
  daily_goal_minutes: number
  preferred_study_times: string[]
  break_reminders: boolean
  auto_save_notes: boolean
}

// Authentication types removed for local setup

// ===== COURSE TYPES =====

export interface Course {
  id: string
  name: string
  description: string
  subject: string
  created_at: string
  updated_at?: string
  is_active: boolean
  tags: string[]
  books_count?: number
  total_study_time?: number
  study_sessions_count?: number
  progress?: CourseProgress
}

export interface CourseCreate {
  name: string
  description: string
  subject: string
  tags?: string[]
}

export interface CourseUpdate {
  name?: string
  description?: string
  subject?: string
  tags?: string[]
  is_active?: boolean
}

export interface CourseProgress {
  total_materials: number
  completed_materials: number
  study_time_minutes: number
  last_study_session?: string
  mastery_level: number // 0-100
}

// ===== BOOK/DOCUMENT TYPES =====

export interface Book {
  id: string
  title: string
  author: string
  description?: string
  year?: string
  publisher?: string
  isbn?: string
  language?: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
  updated_at?: string
  chapters: BookChapter[]
  tags: string[]
  file_path?: string
  file_size?: number
  page_count?: number
  processing_status: ProcessingStatus
}

export interface BookChapter {
  id?: string
  title: string
  summary?: string
  estimated_minutes: number | null
  page_start?: number
  page_end?: number
  has_content: boolean
  key_concepts: string[]
}

export interface BookCreate {
  title: string
  author: string
  description?: string
  year?: string
  publisher?: string
  isbn?: string
  tags?: string[]
}

export interface BookUpdate {
  title?: string
  author?: string
  description?: string
  year?: string
  publisher?: string
  tags?: string[]
}


// ===== STUDY SESSION TYPES =====

export interface StudySession {
  id: string
  course_id: string
  book_id?: string
  start_time: string
  end_time?: string
  duration_minutes: number
  pages_read: number
  notes_taken: number
  topics_covered: string[]
  comprehension_score?: number
  created_at: string
}

export interface StudySessionCreate {
  course_id: string
  book_id?: string
  start_time?: string
  topics_covered?: string[]
}

export interface StudySessionUpdate {
  end_time?: string
  pages_read?: number
  notes_taken?: number
  topics_covered?: string[]
  comprehension_score?: number
}

// ===== CHAT/TUTORING TYPES =====

export interface ChatMessage {
  id: string
  course_id: string
  session_id: string
  message: string
  is_from_user: boolean
  sources?: ChatSource[]
  timestamp: string
  metadata?: Record<string, any>
}

export interface ChatSource {
  book_id: string
  book_title: string
  page_number?: number
  chapter?: string
  relevance_score: number
  excerpt: string
}

export interface ChatRequest {
  message: string
  course_id: string
  session_id?: string
  context?: string[]
}

export interface ChatResponse {
  message: string
  sources: ChatSource[]
  session_id: string
  suggested_followups?: string[]
}

// ===== QUIZ TYPES =====

export interface Quiz {
  id: string
  course_id: string
  title: string
  description?: string
  difficulty: 'easy' | 'medium' | 'hard'
  question_count: number
  time_limit_minutes?: number
  created_at: string
  questions: QuizQuestion[]
}

export interface QuizQuestion {
  id: string
  question: string
  type: 'multiple_choice' | 'true_false' | 'short_answer'
  options?: string[]
  correct_answer: string | number
  explanation?: string
  difficulty: 'easy' | 'medium' | 'hard'
  topic: string
}

export interface QuizRequest {
  course_id: string
  topic?: string
  difficulty?: 'easy' | 'medium' | 'hard'
  question_count: number
  question_types?: string[]
}

export interface QuizSubmission {
  quiz_id: string
  answers: Record<string, string | number>
  time_taken_seconds?: number
}

export interface QuizResult {
  quiz_id: string
  score: number
  total_questions: number
  correct_answers: number
  time_taken_seconds?: number
  feedback: QuizFeedback[]
}

export interface QuizFeedback {
  question_id: string
  is_correct: boolean
  user_answer: string | number
  correct_answer: string | number
  explanation?: string
}

// ===== MIND MAP TYPES =====

export interface MindMap {
  id: string
  course_id: string
  title: string
  description?: string
  topic: string
  nodes: MindMapNode[]
  edges: MindMapEdge[]
  created_at: string
  updated_at?: string
  metadata: Record<string, any>
}

export interface MindMapNode {
  id: string
  title: string
  description?: string
  type: 'concept' | 'topic' | 'detail' | 'reference'
  position: { x: number; y: number }
  color?: string
  size?: 'small' | 'medium' | 'large'
  children?: string[]
  metadata?: Record<string, any>
}

export interface MindMapEdge {
  id: string
  source: string
  target: string
  type: 'relationship' | 'hierarchy' | 'reference'
  label?: string
  weight?: number
}

export interface MindMapRequest {
  course_id: string
  topic: string
  depth?: number
  focus_areas?: string[]
}

// ===== ANALYTICS TYPES =====

export interface StudyAnalytics {
  period_start: string
  period_end: string
  total_study_time: number
  total_sessions: number
  average_session_length: number
  courses_studied: CourseAnalytics[]
  daily_study_times: DailyStudyTime[]
  top_topics: TopicAnalytics[]
  mastery_progress: MasteryProgress[]
}

export interface CourseAnalytics {
  course_id: string
  course_name: string
  study_time_minutes: number
  sessions_count: number
  materials_completed: number
  total_materials: number
  mastery_level: number
  last_study_date: string
}

export interface DailyStudyTime {
  date: string
  study_time_minutes: number
  sessions_count: number
  courses_studied: string[]
}

export interface TopicAnalytics {
  topic: string
  study_time_minutes: number
  mastery_level: number
  questions_asked: number
  accuracy_rate: number
}

export interface MasteryProgress {
  topic: string
  current_level: number
  target_level: number
  progress_rate: number
  estimated_completion_date?: string
}

// ===== API RESPONSE TYPES =====

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: ApiError
  meta?: ResponseMeta
}

export interface ApiError {
  code: string
  message: string
  timestamp: string
  error_id?: string
  details?: Record<string, any>
}

export interface ResponseMeta {
  total?: number
  page?: number
  per_page?: number
  total_pages?: number
  has_next?: boolean
  has_prev?: boolean
}

// ===== PAGINATION TYPES =====

export interface PaginatedRequest {
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  search?: string
  filters?: Record<string, any>
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    total: number
    page: number
    per_page: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

// ===== SEARCH TYPES =====

export interface SearchRequest {
  query: string
  course_id?: string
  search_type?: 'semantic' | 'keyword' | 'hybrid'
  filters?: SearchFilters
  limit?: number
  offset?: number
}

export interface SearchFilters {
  content_types?: ('book' | 'chapter' | 'note')[]
  date_range?: {
    start: string
    end: string
  }
  tags?: string[]
  difficulty?: 'easy' | 'medium' | 'hard'
}

export interface SearchResult {
  id: string
  type: 'book' | 'chapter' | 'note'
  title: string
  content: string
  relevance_score: number
  course_id: string
  course_name: string
  metadata: Record<string, any>
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  search_time_ms: number
  suggestions?: string[]
  facets?: SearchFacet[]
}

export interface SearchFacet {
  field: string
  values: Array<{
    value: string
    count: number
  }>
}

// ===== CONFIGURATION TYPES =====

export interface AppConfig {
  api_base_url: string
  app_name: string
  version: string
  features: AppFeatures
  ui: UiConfig
}

export interface AppFeatures {
  auth_enabled: boolean
  social_features: boolean
  advanced_analytics: boolean
  export_features: boolean
  collaboration: boolean
}

export interface UiConfig {
  theme: {
    default_theme: 'light' | 'dark' | 'system'
    primary_color: string
    accent_color: string
  }
  layout: {
    sidebar_collapsed: boolean
    compact_mode: boolean
    show_animations: boolean
  }
}

// ===== UTILITY TYPES =====

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type SortOrder = 'asc' | 'desc'
export type SortField<T> = keyof T

// ===== EVENT TYPES =====

// User events removed for local setup

// ===== COMPONENT PROP TYPES =====

export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface LoadingProps extends BaseComponentProps {
  isLoading: boolean
  message?: string
}

export interface ErrorProps extends BaseComponentProps {
  error: string | Error
  onRetry?: () => void
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean
  onClose: () => void
  title?: string
}

// Export a union type of all possible entity types (simplified for local)
export type EntityType = 'course' | 'book' | 'session' | 'quiz' | 'mindmap'

// Export commonly used type unions
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type QuizDifficulty = Quiz['difficulty']