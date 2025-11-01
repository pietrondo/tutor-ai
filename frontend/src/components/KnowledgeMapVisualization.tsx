'use client'

import { useState, useEffect, useRef } from 'react'
import { Network, Brain, Target, ArrowRight, Clock, TrendingUp, AlertCircle } from 'lucide-react'
import { Concept, ConceptRelationship, KnowledgeMap, StudyRecommendation } from '@/types/indexing'

interface KnowledgeMapVisualizationProps {
  courseId: string
  selectedConcepts?: string[]
  onConceptSelect?: (conceptId: string) => void
  onRelationshipClick?: (relationship: ConceptRelationship) => void
}

interface Node {
  id: string
  x: number
  y: number
  label: string
  category: string
  difficulty: number
  mastery?: number
  isPrerequisite?: boolean
  isTarget?: boolean
}

interface Edge {
  from: string
  to: string
  type: ConceptRelationship['relationship_type']
  strength: number
}

export function KnowledgeMapVisualization({
  courseId,
  selectedConcepts = [],
  onConceptSelect,
  onRelationshipClick
}: KnowledgeMapVisualizationProps) {
  const [knowledgeMap, setKnowledgeMap] = useState<KnowledgeMap | null>(null)
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    loadKnowledgeMap()
  }, [courseId])

  const loadKnowledgeMap = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch(`/api/courses/${courseId}/knowledge-map`)
      if (!response.ok) {
        throw new Error('Failed to load knowledge map')
      }

      const data: KnowledgeMap = await response.json()
      setKnowledgeMap(data)

      // Process nodes and edges
      const processedNodes = processNodes(data.concepts)
      const processedEdges = processEdges(data.relationships, data.learning_path)

      setNodes(processedNodes)
      setEdges(processedEdges)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load knowledge map')
      console.error('Error loading knowledge map:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const processNodes = (concepts: Concept[]): Node[] => {
    // Create a force-directed layout
    const centerX = 400
    const centerY = 300
    const radius = 200

    return concepts.map((concept, index) => {
      const angle = (index / concepts.length) * 2 * Math.PI
      const distance = radius + (Math.random() - 0.5) * 100

      return {
        id: concept.id,
        x: centerX + Math.cos(angle) * distance,
        y: centerY + Math.sin(angle) * distance,
        label: concept.name,
        category: concept.category,
        difficulty: concept.difficulty,
        mastery: concept.mastery_level,
        isPrerequisite: concept.prerequisites.length > 0,
        isTarget: concept.related_concepts.length > 0
      }
    })
  }

  const processEdges = (relationships: ConceptRelationship[], learningPath: string[]): Edge[] => {
    return relationships.map(rel => ({
      from: rel.source_concept_id,
      to: rel.target_concept_id,
      type: rel.relationship_type,
      strength: rel.strength
    }))
  }

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId === selectedNode ? null : nodeId)
    if (onConceptSelect) {
      onConceptSelect(nodeId)
    }
  }

  const handleEdgeClick = (edge: Edge) => {
    if (onRelationshipClick) {
      // Convert Edge to ConceptRelationship format
      const relationship: ConceptRelationship = {
        source_concept_id: edge.from,
        target_concept_id: edge.to,
        relationship_type: edge.type,
        strength: edge.strength
      }
      onRelationshipClick(relationship)
    }
  }

  const getEdgeColor = (type: ConceptRelationship['relationship_type']) => {
    switch (type) {
      case 'prerequisite': return '#ef4444'
      case 'related': return '#3b82f6'
      case 'application': return '#10b981'
      case 'example': return '#f59e0b'
      case 'contrast': return '#8b5cf6'
      default: return '#6b7280'
    }
  }

  const getEdgeStrokeWidth = (strength: number) => {
    return Math.max(1, strength * 3)
  }

  const getNodeColor = (node: Node) => {
    const isSelected = selectedNode === node.id || selectedConcepts.includes(node.id)
    const isHovered = hoveredNode === node.id

    if (isSelected) return '#3b82f6'
    if (isHovered) return '#2563eb'
    if (node.isPrerequisite) return '#ef4444'
    if (node.isTarget) return '#10b981'
    return '#6b7280'
  }

  const getNodeSize = (node: Node) => {
    const baseSize = 30
    const masteryBonus = node.mastery ? node.mastery * 10 : 0
    return baseSize + masteryBonus
  }

  const renderEdge = (edge: Edge, index: number) => {
    const fromNode = nodes.find(n => n.id === edge.from)
    const toNode = nodes.find(n => n.id === edge.to)

    if (!fromNode || !toNode) return null

    const isSelected = selectedNode === edge.from || selectedNode === edge.to

    return (
      <g key={index}>
        <defs>
          <marker
            id={`arrowhead-${index}`}
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 7 0 7"
              fill={getEdgeColor(edge.type)}
            />
          </marker>
        </defs>
        <line
          x1={fromNode.x}
          y1={fromNode.y}
          x2={toNode.x}
          y2={toNode.y}
          stroke={getEdgeColor(edge.type)}
          strokeWidth={getEdgeStrokeWidth(edge.strength)}
          strokeOpacity={isSelected ? 1 : 0.6}
          markerEnd={`url(#arrowhead-${index})`}
          className="cursor-pointer transition-all duration-200"
          onClick={() => handleEdgeClick(edge)}
        />
      </g>
    )
  }

  const renderNode = (node: Node, index: number) => {
    const isSelected = selectedNode === node.id || selectedConcepts.includes(node.id)
    const isHovered = hoveredNode === node.id
    const size = getNodeSize(node)

    return (
      <g key={index}>
        {/* Connection circle for hover effect */}
        {isHovered && (
          <circle
            cx={node.x}
            cy={node.y}
            r={size + 10}
            fill={getNodeColor(node)}
            fillOpacity={0.2}
          />
        )}

        {/* Node circle */}
        <circle
          cx={node.x}
          cy={node.y}
          r={size}
          fill={getNodeColor(node)}
          stroke="#ffffff"
          strokeWidth={2}
          className="cursor-pointer transition-all duration-200"
          onClick={() => handleNodeClick(node.id)}
          onMouseEnter={() => setHoveredNode(node.id)}
          onMouseLeave={() => setHoveredNode(null)}
        />

        {/* Node label */}
        <text
          x={node.x}
          y={node.y}
          textAnchor="middle"
          dominantBaseline="middle"
          className="text-xs font-medium pointer-events-none"
          fill="white"
        >
          {node.label.length > 15 ? node.label.substring(0, 12) + '...' : node.label}
        </text>

        {/* Difficulty indicator */}
        <circle
          cx={node.x + size - 5}
          cy={node.y - size + 5}
          r={4}
          fill={
            node.difficulty === 1 ? '#10b981' :
            node.difficulty === 2 ? '#3b82f6' :
            node.difficulty === 3 ? '#f59e0b' :
            node.difficulty === 4 ? '#f97316' :
            '#ef4444'
          }
        />

        {/* Mastery indicator */}
        {node.mastery && (
          <circle
            cx={node.x - size + 5}
            cy={node.y - size + 5}
            r={4}
            fill="#10b981"
          />
        )}

        {/* Prerequisite indicator */}
        {node.isPrerequisite && (
          <circle
            cx={node.x}
            cy={node.y - size - 10}
            r={3}
            fill="#ef4444"
          />
        )}
      </g>
    )
  }

  const renderLegend = () => {
    return (
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 space-y-3">
        <h5 className="text-sm font-semibold text-gray-900">Legenda</h5>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-xs text-gray-600">Prerequisito</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-xs text-gray-600">Correlato</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-teal-500"></div>
            <span className="text-xs text-gray-600">Applicazione</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-amber-500"></div>
            <span className="text text-gray-600">Esempio</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-purple-500"></div>
            <span className="text-xs text-gray-600">Contrasto</span>
          </div>
        </div>

        <div className="border-t pt-3 space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-xs text-gray-600">Mastery alta</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-xs text-gray-600">Mastery bassa</span>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="glass rounded-2xl p-8 border border-gray-200/50 text-center">
        <Network className="h-8 w-8 text-blue-600 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Caricamento mappatura delle conoscenze...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass rounded-2xl p-8 border border-gray-200/50 text-center">
        <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadKnowledgeMap}
          className="btn btn-primary btn-sm mt-4"
        >
          Riprova
        </button>
      </div>
    )
  }

  return (
    <div className="glass rounded-2xl p-6 border border-gray-200/50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg text-gray-900">
          Mappatura delle Conoscenze
        </h3>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Brain className="h-4 w-4" />
          <span>{nodes.length} concetti</span>
          <span>•</span>
          <span>{edges.length} relazioni</span>
        </div>
      </div>

      <div className="relative bg-gray-50 rounded-xl border border-gray-200" style={{ height: '500px' }}>
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 800 600"
          className="rounded-xl"
        >
          {/* Grid background */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="800" height="600" fill="url(#grid)" />

          {/* Render edges */}
          {edges.map((edge, index) => renderEdge(edge, index))}

          {/* Render nodes */}
          {nodes.map((node, index) => renderNode(node, index))}
        </svg>

        {/* Legend */}
        {renderLegend()}
      </div>

      {/* Selected Concept Details */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm">
          <h4 className="font-semibold text-gray-900 mb-2">
            {nodes.find(n => n.id === selectedNode)?.label}
          </h4>
          <div className="space-y-1 text-sm text-gray-600">
            <p>Categoria: {nodes.find(n => n.id === selectedNode)?.category}</p>
            <p>Difficoltà: {nodes.find(n => n.id === selectedNode)?.difficulty}/5</p>
            {nodes.find(n => n.id === selectedNode)?.mastery && (
              <p>Mastery: {Math.round((nodes.find(n => n.id === selectedNode)?.mastery || 0) * 100)}%</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}