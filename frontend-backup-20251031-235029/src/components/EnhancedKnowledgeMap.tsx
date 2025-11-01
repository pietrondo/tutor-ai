'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Network,
  Brain,
  Target,
  TrendingUp,
  Zap,
  RefreshCw,
  Settings,
  Play,
  ArrowSync,
  Cpu,
  Globe,
  Database,
  Activity,
  BarChart3,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { Concept, ConceptRelationship, KnowledgeMap } from '@/types/indexing'

interface EnhancedKnowledgeMapProps {
  courseId: string
  concepts: Concept[]
  relationships: ConceptRelationship[]
  onConceptSelect?: (conceptId: string) => void
  onRelationshipClick?: (relationship: ConceptRelationship) => void
}

interface EnhancedNode extends Concept {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  context7Data: {
    latestTrends: string[]
    industryRelevance: number
    realWorldApplications: string[]
    learningResources: LearningResource[]
  }
  realTimeData: {
    lastAccessed: string
    accessFrequency: number
    masteryTrend: 'improving' | 'stable' | 'declining'
    communityInterest: number
  }
}

interface LearningResource {
  type: 'documentation' | 'tutorial' | 'video' | 'article'
  title: string
  url: string
  difficulty: number
  duration: number
  rating: number
}

interface EnhancedEdge extends ConceptRelationship {
  strength: number
  context7Insights: {
    collaborationPatterns: string[]
    workflowIntegration: string[]
    bestPractices: string[]
  }
  realTimeMetrics: {
    traversalFrequency: number
    learningPathEfficiency: number
    difficultyPrediction: number
  }
}

interface Context7MapConfig {
  showRealTimeUpdates: boolean
  includeIndustryTrends: boolean
  displayLearningResources: boolean
  enablePredictiveAnalytics: boolean
  showCommunityData: boolean
  animateTransitions: boolean
}

export function EnhancedKnowledgeMap({
  courseId,
  concepts,
  relationships,
  onConceptSelect,
  onRelationshipClick
}: EnhancedKnowledgeMapProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const animationRef = useRef<number>()
  const [enhancedNodes, setEnhancedNodes] = useState<EnhancedNode[]>([])
  const [enhancedEdges, setEnhancedEdges] = useState<EnhancedEdge[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [context7Config, setContext7Config] = useState<Context7MapConfig>({
    showRealTimeUpdates: true,
    includeIndustryTrends: true,
    displayLearningResources: true,
    enablePredictiveAnalytics: true,
    showCommunityData: true,
    animateTransitions: true
  })
  const [showConfig, setShowConfig] = useState(false)
  const [viewMode, setViewMode] = useState<'standard' | 'trends' | 'analytics' | 'community'>('standard')

  useEffect(() => {
    initializeEnhancedMap()
    if (context7Config.showRealTimeUpdates) {
      startRealTimeUpdates()
    }
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [concepts, relationships, context7Config])

  const initializeEnhancedMap = async () => {
    setIsLoading(true)

    // Create enhanced nodes with Context7 data
    const nodes = await createEnhancedNodes()
    const edges = await createEnhancedEdges()

    setEnhancedNodes(nodes)
    setEnhancedEdges(edges)

    // Start physics simulation
    if (context7Config.animateTransitions) {
      startPhysicsSimulation()
    }

    setIsLoading(false)
  }

  const createEnhancedNodes = async (): Promise<EnhancedNode[]> => {
    const centerX = 400
    const centerY = 300
    const radius = 200

    return Promise.all(concepts.map(async (concept, index) => {
      const angle = (index / concepts.length) * 2 * Math.PI
      const distance = radius + (Math.random() - 0.5) * 100

      // Fetch Context7 enhancements for each concept
      const context7Data = await fetchContext7Data(concept)
      const realTimeData = await fetchRealTimeData(concept)

      return {
        ...concept,
        x: centerX + Math.cos(angle) * distance,
        y: centerY + Math.sin(angle) * distance,
        vx: 0,
        vy: 0,
        radius: 20 + (concept.mastery_level || 0) * 15,
        context7Data,
        realTimeData
      }
    }))
  }

  const createEnhancedEdges = async (): Promise<EnhancedEdge[]> => {
    return Promise.all(relationships.map(async (rel) => {
      const context7Insights = await fetchEdgeContext7Data(rel)
      const realTimeMetrics = await fetchEdgeRealTimeMetrics(rel)

      return {
        ...rel,
        strength: rel.strength,
        context7Insights,
        realTimeMetrics
      }
    }))
  }

  const fetchContext7Data = async (concept: Concept): Promise<EnhancedNode['context7Data']> => {
    // Simulate Context7 API call for concept enhancements
    await new Promise(resolve => setTimeout(resolve, 200))

    return {
      latestTrends: [
        'AI integration in web development',
        'Serverless architecture adoption',
        'Progressive Web Apps evolution',
        'Microservices best practices'
      ],
      industryRelevance: Math.random() * 0.5 + 0.5,
      realWorldApplications: [
        'Enterprise software solutions',
        'E-commerce platforms',
        'Real-time data processing',
        'Mobile application development'
      ],
      learningResources: [
        {
          type: 'documentation',
          title: `Official ${concept.name} Documentation`,
          url: `https://docs.example.com/${concept.id}`,
          difficulty: concept.difficulty,
          duration: 30,
          rating: 4.5
        },
        {
          type: 'tutorial',
          title: `Complete ${concept.name} Tutorial`,
          url: `https://tutorial.example.com/${concept.id}`,
          difficulty: concept.difficulty,
          duration: 45,
          rating: 4.7
        }
      ]
    }
  }

  const fetchRealTimeData = async (concept: Concept): Promise<EnhancedNode['realTimeData']> => {
    await new Promise(resolve => setTimeout(resolve, 100))

    return {
      lastAccessed: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      accessFrequency: Math.floor(Math.random() * 100) + 1,
      masteryTrend: ['improving', 'stable', 'declining'][Math.floor(Math.random() * 3)] as any,
      communityInterest: Math.random()
    }
  }

  const fetchEdgeContext7Data = async (rel: ConceptRelationship): Promise<EnhancedEdge['context7Insights']> => {
    await new Promise(resolve => setTimeout(resolve, 150))

    return {
      collaborationPatterns: [
        'Sequential learning recommended',
        'Parallel study possible',
        'Cross-reference beneficial'
      ],
      workflowIntegration: [
        'Agile development workflow',
        'CI/CD pipeline integration',
        'Code review processes'
      ],
      bestPractices: [
        'Master prerequisites first',
        'Practice with real projects',
        'Join community discussions'
      ]
    }
  }

  const fetchEdgeRealTimeMetrics = async (rel: ConceptRelationship): Promise<EnhancedEdge['realTimeMetrics']> => {
    await new Promise(resolve => setTimeout(resolve, 100))

    return {
      traversalFrequency: Math.floor(Math.random() * 50) + 1,
      learningPathEfficiency: Math.random(),
      difficultyPrediction: rel.strength * 5
    }
  }

  const startPhysicsSimulation = () => {
    const simulate = () => {
      setEnhancedNodes(prevNodes => {
        const newNodes = [...prevNodes]
        const damping = 0.95
        const repulsion = 5000
        const attraction = 0.001

        // Apply forces
        for (let i = 0; i < newNodes.length; i++) {
          let fx = 0
          let fy = 0

          // Repulsion between nodes
          for (let j = 0; j < newNodes.length; j++) {
            if (i !== j) {
              const dx = newNodes[i].x - newNodes[j].x
              const dy = newNodes[i].y - newNodes[j].y
              const distance = Math.sqrt(dx * dx + dy * dy)
              if (distance > 0) {
                const force = repulsion / (distance * distance)
                fx += (dx / distance) * force
                fy += (dy / distance) * force
              }
            }
          }

          // Attraction to center
          const dx = 400 - newNodes[i].x
          const dy = 300 - newNodes[i].y
          fx += dx * attraction
          fy += dy * attraction

          // Update velocity and position
          newNodes[i].vx = (newNodes[i].vx + fx) * damping
          newNodes[i].vy = (newNodes[i].vy + fy) * damping
          newNodes[i].x += newNodes[i].vx
          newNodes[i].y += newNodes[i].vy
        }

        return newNodes
      })

      animationRef.current = requestAnimationFrame(simulate)
    }

    simulate()
  }

  const startRealTimeUpdates = () => {
    const interval = setInterval(async () => {
      // Update real-time data for a random subset of nodes
      const nodesToUpdate = enhancedNodes.slice(0, Math.ceil(enhancedNodes.length / 3))

      const updatedNodes = await Promise.all(
        enhancedNodes.map(async (node) => {
          if (nodesToUpdate.includes(node)) {
            const realTimeData = await fetchRealTimeData(node)
            return { ...node, realTimeData }
          }
          return node
        })
      )

      setEnhancedNodes(updatedNodes)
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(selectedNode === nodeId ? null : nodeId)
    if (onConceptSelect) {
      onConceptSelect(nodeId)
    }
  }

  const getNodeColor = (node: EnhancedNode) => {
    const isSelected = selectedNode === node.id
    const isHovered = hoveredNode === node.id

    if (isSelected) return '#8b5cf6' // Purple for selected
    if (isHovered) return '#7c3aed' // Lighter purple for hover

    // Color based on view mode
    switch (viewMode) {
      case 'trends':
        return node.context7Data.industryRelevance > 0.7 ? '#10b981' : '#6b7280'
      case 'analytics':
        return node.realTimeData.masteryTrend === 'improving' ? '#10b981' :
               node.realTimeData.masteryTrend === 'declining' ? '#ef4444' : '#6b7280'
      case 'community':
        return node.realTimeData.communityInterest > 0.5 ? '#f59e0b' : '#6b7280'
      default:
        return node.mastery_level && node.mastery_level > 0.7 ? '#10b981' : '#6b7280'
    }
  }

  const renderNode = (node: EnhancedNode) => {
    const isSelected = selectedNode === node.id
    const isHovered = hoveredNode === node.id
    const color = getNodeColor(node)

    return (
      <g key={node.id}>
        {/* Glow effect for selected/hovered nodes */}
        {(isSelected || isHovered) && (
          <circle
            cx={node.x}
            cy={node.y}
            r={node.radius + 10}
            fill={color}
            fillOpacity={0.2}
            className="transition-all duration-300"
          />
        )}

        {/* Main node circle */}
        <circle
          cx={node.x}
          cy={node.y}
          r={node.radius}
          fill={color}
          stroke="#ffffff"
          strokeWidth={2}
          className="cursor-pointer transition-all duration-300"
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
          className="text-xs font-medium pointer-events-none fill-white"
        >
          {node.name.length > 12 ? node.name.substring(0, 9) + '...' : node.name}
        </text>

        {/* Indicators based on view mode */}
        {viewMode === 'trends' && context7Config.includeIndustryTrends && (
          <circle
            cx={node.x + node.radius - 5}
            cy={node.y - node.radius + 5}
            r={4}
            fill={node.context7Data.industryRelevance > 0.7 ? '#10b981' : '#f59e0b'}
          />
        )}

        {viewMode === 'analytics' && context7Config.showRealTimeUpdates && (
          <g transform={`translate(${node.x - node.radius + 5}, ${node.y - node.radius + 5})`}>
            {node.realTimeData.masteryTrend === 'improving' && (
              <TrendingUp className="h-4 w-4 text-green-600" />
            )}
            {node.realTimeData.masteryTrend === 'declining' && (
              <TrendingUp className="h-4 w-4 text-red-600 transform rotate-180" />
            )}
          </g>
        )}

        {viewMode === 'community' && context7Config.showCommunityData && (
          <circle
            cx={node.x}
            cy={node.y + node.radius + 8}
            r={3}
            fill={node.realTimeData.communityInterest > 0.5 ? '#f59e0b' : '#6b7280'}
          />
        )}
      </g>
    )
  }

  const renderEdge = (edge: EnhancedEdge) => {
    const fromNode = enhancedNodes.find(n => n.id === edge.source_concept_id)
    const toNode = enhancedNodes.find(n => n.id === edge.target_concept_id)

    if (!fromNode || !toNode) return null

    const isSelected = selectedNode === edge.source_concept_id || selectedNode === edge.target_concept_id
    const color = edge.relationship_type === 'prerequisite' ? '#ef4444' :
                  edge.relationship_type === 'related' ? '#3b82f6' :
                  edge.relationship_type === 'application' ? '#10b981' : '#6b7280'

    return (
      <g key={`${edge.source_concept_id}-${edge.target_concept_id}`}>
        <defs>
          <marker
            id={`arrowhead-${edge.source_concept_id}-${edge.target_concept_id}`}
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 7 0 7"
              fill={color}
            />
          </marker>
        </defs>
        <line
          x1={fromNode.x}
          y1={fromNode.y}
          x2={toNode.x}
          y2={toNode.y}
          stroke={color}
          strokeWidth={edge.strength * 3}
          strokeOpacity={isSelected ? 1 : 0.6}
          markerEnd={`url(#arrowhead-${edge.source_concept_id}-${edge.target_concept_id})`}
          className="cursor-pointer transition-all duration-200"
        />

        {/* Real-time metrics overlay */}
        {context7Config.showRealTimeUpdates && viewMode === 'analytics' && (
          <g>
            <circle
              cx={(fromNode.x + toNode.x) / 2}
              cy={(fromNode.y + toNode.y) / 2}
              r={3}
              fill="#fbbf24"
            />
            <text
              x={(fromNode.x + toNode.x) / 2}
              y={(fromNode.y + toNode.y) / 2 - 8}
              textAnchor="middle"
              className="text-xs fill-gray-600"
            >
              {edge.realTimeMetrics.traversalFrequency}
            </text>
          </g>
        )}
      </g>
    )
  }

  const renderNodeDetails = () => {
    if (!selectedNode) return null

    const node = enhancedNodes.find(n => n.id === selectedNode)
    if (!node) return null

    return (
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm max-h-96 overflow-y-auto">
        <h4 className="font-semibold text-gray-900 mb-3">{node.name}</h4>

        {/* Basic Info */}
        <div className="space-y-2 text-sm text-gray-600 mb-4">
          <p><strong>Categoria:</strong> {node.category}</p>
          <p><strong>Difficoltà:</strong> {node.difficulty}/5</p>
          <p><strong>Mastery:</strong> {Math.round((node.mastery_level || 0) * 100)}%</p>
        </div>

        {/* Context7 Insights */}
        {context7Config.includeIndustryTrends && (
          <div className="mb-4">
            <h5 className="font-medium text-gray-900 mb-2 flex items-center">
              <Zap className="h-4 w-4 mr-2 text-purple-600" />
              Context7 Insights
            </h5>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-600">Industry Relevance</span>
                  <span className="text-xs text-purple-600">{Math.round(node.context7Data.industryRelevance * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div
                    className="bg-purple-500 h-1 rounded-full"
                    style={{ width: `${node.context7Data.industryRelevance * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Real-time Data */}
        {context7Config.showRealTimeUpdates && (
          <div className="mb-4">
            <h5 className="font-medium text-gray-900 mb-2 flex items-center">
              <Activity className="h-4 w-4 mr-2 text-blue-600" />
              Real-time Data
            </h5>
            <div className="space-y-1 text-xs text-gray-600">
              <p><strong>Access Frequency:</strong> {node.realTimeData.accessFrequency} times</p>
              <p><strong>Mastery Trend:</strong>
                <span className={`ml-1 ${
                  node.realTimeData.masteryTrend === 'improving' ? 'text-green-600' :
                  node.realTimeData.masteryTrend === 'declining' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {node.realTimeData.masteryTrend}
                </span>
              </p>
              <p><strong>Community Interest:</strong> {Math.round(node.realTimeData.communityInterest * 100)}%</p>
            </div>
          </div>
        )}

        {/* Learning Resources */}
        {context7Config.displayLearningResources && (
          <div>
            <h5 className="font-medium text-gray-900 mb-2 flex items-center">
              <BookOpen className="h-4 w-4 mr-2 text-green-600" />
              Learning Resources
            </h5>
            <div className="space-y-2">
              {node.context7Data.learningResources.slice(0, 2).map((resource, index) => (
                <div key={index} className="p-2 bg-gray-50 rounded text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900">{resource.type}</span>
                    <span className="text-gray-500">⭐ {resource.rating}</span>
                  </div>
                  <p className="text-gray-600">{resource.title}</p>
                  <p className="text-gray-500">{resource.duration}min • Difficulty {resource.difficulty}/5</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
              <Network className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Enhanced Knowledge Map
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Mappatura conoscenze potenziata con Context7 e dati real-time
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="btn btn-secondary btn-sm"
            >
              <Settings className="h-4 w-4 mr-2" />
              Configurazione
            </button>
            <button
              onClick={initializeEnhancedMap}
              disabled={isLoading}
              className="btn btn-primary btn-sm"
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowSync className="h-4 w-4 mr-2" />
              )}
              Aggiorna
            </button>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {[
            { id: 'standard', label: 'Standard', icon: Network },
            { id: 'trends', label: 'Trend', icon: TrendingUp },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'community', label: 'Community', icon: Globe }
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setViewMode(mode.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ${
                viewMode === mode.id
                  ? 'bg-white text-purple-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <mode.icon className="h-4 w-4" />
              <span className="text-sm font-medium">{mode.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Configurazione Context7</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(context7Config).map(([key, value]) => (
              <label key={key} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(e) => setContext7Config(prev => ({ ...prev, [key]: e.target.checked }))}
                  className="form-checkbox"
                />
                <span className="text-sm text-gray-700">
                  {key === 'showRealTimeUpdates' ? 'Aggiornamenti Real-time' :
                   key === 'includeIndustryTrends' ? 'Trend di Settore' :
                   key === 'displayLearningResources' ? 'Risorse di Apprendimento' :
                   key === 'enablePredictiveAnalytics' ? 'Analytics Predittive' :
                   key === 'showCommunityData' ? 'Dati Community' :
                   'Animazioni Fluide'}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Knowledge Map */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="relative bg-gray-50 rounded-xl border border-gray-200" style={{ height: '600px' }}>
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
            {enhancedEdges.map((edge) => renderEdge(edge))}

            {/* Render nodes */}
            {enhancedNodes.map((node) => renderNode(node))}
          </svg>

          {/* Node Details Panel */}
          {renderNodeDetails()}

          {/* Real-time Update Indicator */}
          {context7Config.showRealTimeUpdates && (
            <div className="absolute top-4 right-4 flex items-center space-x-2 bg-white rounded-lg shadow-lg px-3 py-2">
              <Activity className="h-4 w-4 text-green-600 animate-pulse" />
              <span className="text-sm text-gray-600">Real-time</span>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-purple-500"></div>
            <span className="text-sm text-gray-600">Selezionato</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-600">
              {viewMode === 'trends' ? 'Alta Rilevanza' :
               viewMode === 'analytics' ? 'In Miglioramento' :
               viewMode === 'community' ? 'Alto Interesse' : 'Alta Mastery'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-sm text-gray-600">Prerequisito</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-sm text-gray-600">Correlato</span>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {enhancedNodes.length}
            </div>
            <p className="text-sm text-gray-500">Concetti Enhanced</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {enhancedEdges.length}
            </div>
            <p className="text-sm text-gray-500">Relazioni Analizzate</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {enhancedNodes.filter(n => n.context7Data.industryRelevance > 0.7).length}
            </div>
            <p className="text-sm text-gray-500">Alta Rilevanza</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {enhancedNodes.filter(n => n.realTimeData.masteryTrend === 'improving').length}
            </div>
            <p className="text-sm text-gray-500">In Miglioramento</p>
          </div>
        </div>
      </div>
    </div>
  )
}