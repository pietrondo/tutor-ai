export interface CourseConceptChapter {
  title: string
  index?: number | null
}

export interface CourseConcept {
  id: string
  name: string
  summary: string
  chapter: CourseConceptChapter
  related_topics: string[]
  learning_objectives: string[]
  suggested_reading: string[]
  recommended_minutes: number
  quiz_outline: string[]
}

export interface CourseConceptMap {
  course_id: string
  generated_at: string
  concepts: CourseConcept[]
}

export interface ConceptQuizAttempt {
  timestamp: string
  score: number
  time_seconds: number
  correct_answers: number
  total_questions: number
}

export interface ConceptMetricsSummary {
  average_score: number
  average_time_seconds: number
  attempts_count: number
  best_score: number
  latest_score: number
  latest_attempt_at: string | null
}

export interface ConceptMetricsEntry {
  concept_name: string
  chapter_title?: string | null
  attempts: ConceptQuizAttempt[]
  stats: ConceptMetricsSummary
}

export type ConceptMetrics = Record<string, ConceptMetricsEntry>
