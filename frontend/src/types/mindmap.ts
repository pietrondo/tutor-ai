export interface MindMapNode {
  id: string
  type: 'central' | 'topic' | 'subtopic' | 'example' | 'connection'
  position: { x: number; y: number }
  data: {
    label: string
    description?: string
    color?: string
    fontSize?: number
    expanded?: boolean
    topics?: string[]
    examples?: string[]
    connections?: string[]
    importance?: 'high' | 'medium' | 'low'
  }
  style?: {
    backgroundColor?: string
    border?: string
    borderRadius?: number
    fontSize?: number
    color?: string
  }
}

export interface MindMapEdge {
  id: string
  source: string
  target: string
  type: 'hierarchy' | 'connection' | 'example'
  data: {
    label?: string
    relationship?: string
    strength?: number
  }
  style?: {
    stroke?: string
    strokeWidth?: number
    strokeDasharray?: string
  }
}

export interface MindMap {
  id: string
  sessionId: string
  title: string
  description?: string
  nodes: MindMapNode[]
  edges: MindMapEdge[]
  metadata: {
    createdAt: string
    updatedAt: string
    version: string
    author: string
    tags?: string[]
    difficulty?: 'beginner' | 'intermediate' | 'advanced'
    sessionTitle?: string
    courseId?: string
  }
  layout: {
    type: 'radial' | 'hierarchical' | 'force' | 'mindmap'
    nodeSpacing?: number
    levelSpacing?: number
    direction?: 'TB' | 'LR' | 'RL' | 'BT'
  }
  style: {
    theme: 'light' | 'dark' | 'colorful' | 'minimal'
    fontFamily?: string
    nodeBaseSize?: number
    edgeBaseSize?: number
  }
}

export interface MindMapGenerationPrompt {
  title: string
  context: string
  objectives?: string[]
  topics?: string[]
  difficulty?: string
  preferredStructure?: 'radial' | 'hierarchical'
  includeExamples?: boolean
  includeConnections?: boolean
}

export interface MindMapAIRequest {
  sessionId: string
  sessionTitle: string
  sessionContext: {
    description: string
    objectives: string[]
    topics: string[]
    difficulty: string
    duration_minutes: number
  }
  customPrompt?: string
  preferences?: {
    structure: 'radial' | 'hierarchical'
    detailLevel: 'basic' | 'detailed' | 'comprehensive'
    includeExamples: boolean
    maxNodes?: number
  }
}

export interface StudyMindmapNode {
  id: string
  title: string
  summary?: string
  ai_hint?: string
  study_actions: string[]
  priority?: number | null
  references?: string[]
  children: StudyMindmapNode[]
  recurrence?: number
  synonyms?: string[]
  session_metadata?: NodeSessionMetadata
  progress_data?: NodeProgressData
}

export interface NodeSessionMetadata {
  priority_adjusted: boolean
  mastery_level?: number
  recently_studied: boolean
  weak_area: boolean
  recommended_action: 'focused_review' | 'practice_application' | 'foundational_review' | 'normal_study'
}

export interface NodeProgressData {
  completion_percentage: number
  last_studied?: string
  next_review?: string
  performance_metrics?: {
    accuracy: number
    time_spent: number
    attempts: number
  }
  study_time_total: number
  review_count: number
  confidence_level: number
}

export interface StudyPlanPhase {
  phase: string
  objective?: string
  activities: string[]
  ai_support?: string
  duration_minutes?: number | null
}

export interface StudyMindmap {
  title: string
  overview?: string
  nodes: StudyMindmapNode[]
  study_plan: StudyPlanPhase[]
  references?: string[]
  session_guidance?: SessionGuidance
  cognitive_load_level?: string
  knowledge_type?: string
  session_aware?: boolean
  learning_optimizations?: LearningOptimizations
}

export interface SessionGuidance {
  focus_on_weak_areas: boolean
  recommended_study_order: string[]
  estimated_study_time: {
    total_minutes: number
    breakdown: {
      weak_areas: number
      review: number
      new_concepts: number
    }
    adjusted_for_fatigue: boolean
  }
  adaptive_suggestions: string[]
}

export interface LearningOptimizations {
  max_branches_per_node: number
  total_concepts: number
  cognitive_load_level: string
  knowledge_type: string
  dual_coding_applied?: boolean
  scaffolding_included?: boolean
  metacognitive_prompts?: boolean
  retrieval_practice?: boolean
}

export interface StudySessionContext {
  session_id?: string
  course_id?: string
  book_id?: string
  current_progress: number
  weak_areas: string[]
  mastery_levels: Record<string, number>
  quiz_performance: Record<string, number>
  study_time_today: number
  preferred_difficulty: string
  recently_studied: string[]
  goals: string[]
}

export interface ExpandedStudyNode {
  id: string
  title: string
  summary?: string
  ai_hint?: string
  study_actions: string[]
  priority?: number | null
  references?: string[]
}
