export interface ContentChunk {
  id: string
  material_id: string
  content: string
  chunk_index: number
  start_page?: number
  end_page?: number
  embedding?: number[]
  concepts: string[]
  difficulty_level: 1 | 2 | 3 | 4 | 5
  content_type: 'text' | 'heading' | 'list' | 'table' | 'image' | 'formula'
  metadata: {
    word_count: number
    sentence_count: number
    key_terms: string[]
    summary: string
  }
  created_at: string
  updated_at: string
}

export interface Concept {
  id: string
  name: string
  definition: string
  category: string
  difficulty: 1 | 2 | 3 | 4 | 5
  prerequisites: string[]
  related_concepts: string[]
  material_chunks: string[]
  mastery_level?: number
  last_reviewed?: string
}

export interface KnowledgeMap {
  id: string
  course_id: string
  concepts: Concept[]
  relationships: ConceptRelationship[]
  learning_path: string[]
  created_at: string
  updated_at: string
}

export interface ConceptRelationship {
  source_concept_id: string
  target_concept_id: string
  relationship_type: 'prerequisite' | 'related' | 'application' | 'example' | 'contrast'
  strength: number // 0-1
}

export interface TestQuestion {
  id: string
  concept_id: string
  material_chunk_id: string
  question: string
  type: 'multiple_choice' | 'true_false' | 'short_answer' | 'essay' | 'fill_blank' | 'matching'
  difficulty: 1 | 2 | 3 | 4 | 5
  options?: string[]
  correct_answer: string | string[]
  explanation: string
  hints: string[]
  time_limit?: number // seconds
  points: number
  tags: string[]
  created_at: string
}

export interface TestSession {
  id: string
  user_id: string
  course_id: string
  questions: TestQuestion[]
  started_at: string
  completed_at?: string
  score?: number
  answers: TestAnswer[]
  time_spent: number // seconds
  concept_mastery: Record<string, number>
}

export interface TestAnswer {
  question_id: string
  answer: string | string[]
  is_correct: boolean
  time_taken: number
  confidence?: number // 1-5
  attempts: number
}

export interface UserProgress {
  id: string
  user_id: string
  course_id: string
  concept_mastery: Record<string, {
    level: number // 0-1
    last_reviewed: string
    review_count: number
    average_confidence: number
  }>
  learning_objectives: LearningObjective[]
  study_time: {
    total_minutes: number
    last_7_days: number
    last_30_days: number
  }
  test_performance: {
    total_tests: number
    average_score: number
    improvement_rate: number
    weak_concepts: string[]
    strong_concepts: string[]
  }
  created_at: string
  updated_at: string
}

export interface LearningObjective {
  id: string
  description: string
  concept_ids: string[]
  target_mastery: number
  current_mastery: number
  due_date?: string
  status: 'not_started' | 'in_progress' | 'completed' | 'mastered'
}

export interface MaterialIndexingStatus {
  material_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_chunks: number
  processed_chunks: number
  extracted_concepts: number
  generated_questions: number
  error_message?: string
  processing_started_at?: string
  completed_at?: string
}

export interface StudyRecommendation {
  concept_id: string
  priority: 'high' | 'medium' | 'low'
  reason: string
  recommended_materials: string[]
  suggested_study_method: 'review' | 'practice' | 'teach' | 'apply'
  estimated_time: number // minutes
}

export interface ContentAnalysisResult {
  material_id: string
  summary: string
  key_concepts: string[]
  difficulty_distribution: Record<number, number>
  content_types: Record<string, number>
  estimated_study_time: number
  prerequisite_concepts: string[]
  learning_objectives: string[]
}

export interface ConceptMasteryVerification {
  id: string
  user_id: string
  concept_id: string
  session_data: any
  mastery_level: number
  score: number
  verified_at: string
  verification_type: 'automated_test' | 'manual_assessment' | 'peer_review'
  confidence_score: number
  improvement_suggestions: string[]
}