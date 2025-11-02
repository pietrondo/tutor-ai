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