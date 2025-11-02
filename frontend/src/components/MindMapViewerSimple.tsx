'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  ConnectionMode,
  Panel,
  ReactFlowProvider,
} from 'reactflow'
import html2canvas from 'html2canvas'
import {
  Brain,
  Plus,
  Minus,
  Maximize2,
  Download,
  MessageSquare,
  Zap,
  Lightbulb,
  Target,
  BookOpen,
  RefreshCw,
  Save,
  Share2,
  Eye,
  EyeOff,
  Settings,
  ChevronDown,
  Circle,
  Square,
  Hexagon,
  Triangle,
  Star,
  CheckCircle2,
  Minimize2
} from 'lucide-react'
import 'reactflow/dist/style.css'

// Interfacce semplificate
interface SimpleMindMapNode {
  id: string
  type: 'central' | 'topic' | 'subtopic' | 'example' | 'connection'
  position: { x: number; y: number }
  data: {
    label: string
    description?: string
    type: string
    importance?: 'high' | 'medium' | 'low'
    topics?: string[]
    examples?: string[]
  }
}

interface SimpleMindMap {
  id: string
  sessionId: string
  title: string
  description?: string
  nodes: SimpleMindMapNode[]
  edges: any[]
  metadata: {
    createdAt: string
    updatedAt: string
    version: string
    author: string
  }
  layout: {
    type: 'radial' | 'hierarchical' | 'force' | 'mindmap'
  }
  style: {
    theme: 'light' | 'dark' | 'colorful' | 'minimal'
  }
}

// Custom node component
const SimpleMindMapNodeComponent = ({ data, selected }: { data: any; selected: boolean }) => {
  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'central': return <Brain className="w-5 h-5" />
      case 'topic': return <BookOpen className="w-4 h-4" />
      case 'subtopic': return <Target className="w-3 h-3" />
      case 'example': return <Lightbulb className="w-3 h-3" />
      case 'connection': return <Zap className="w-3 h-3" />
      default: return <Circle className="w-4 h-4" />
    }
  }

  const getNodeColor = (type: string, importance?: string) => {
    if (type === 'central') return 'bg-gradient-to-br from-blue-500 to-purple-600'

    const colorMap = {
      high: 'bg-gradient-to-br from-red-500 to-orange-500',
      medium: 'bg-gradient-to-br from-yellow-500 to-green-500',
      low: 'bg-gradient-to-br from-blue-500 to-cyan-500'
    }

    return colorMap[importance as keyof typeof colorMap] || colorMap.medium
  }

  const getNodeShape = (type: string) => {
    switch (type) {
      case 'central': return 'rounded-full'
      case 'topic': return 'rounded-lg'
      case 'subtopic': return 'rounded-md'
      default: return 'rounded-full'
    }
  }

  return (
    <div className={`p-3 min-w-[120px] max-w-[250px] ${selected ? 'ring-2 ring-blue-400 ring-offset-2' : ''} ${getNodeShape(data.type)} ${getNodeColor(data.type, data.importance)} text-white shadow-lg transition-all duration-200 hover:shadow-xl`}>
      <div className="flex items-start space-x-2">
        <div className="flex-shrink-0 mt-0.5">
          {getNodeIcon(data.type)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm text-white line-clamp-2">
            {data.label}
          </div>
          {data.description && (
            <div className="text-xs text-white/80 mt-1 line-clamp-2">
              {data.description}
            </div>
          )}
          {data.topics && data.topics.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {data.topics.slice(0, 2).map((topic: string, index: number) => (
                <span key={index} className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                  {topic}
                </span>
              ))}
              {data.topics.length > 2 && (
                <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                  +{data.topics.length - 2}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Componente principale
const SimpleMindMapViewer: React.FC<{
  mindMap: SimpleMindMap
  onMindMapChange?: (mindMap: SimpleMindMap) => void
  readOnly?: boolean
  enableEditing?: boolean
  className?: string
}> = ({
  mindMap,
  onMindMapChange,
  readOnly = false,
  enableEditing = true,
  className = ''
}) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(mindMap.nodes as Node[])
  const [edges, setEdges, onEdgesChange] = useEdgesState(mindMap.edges as Edge[])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showControls, setShowControls] = useState(true)

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const exportImage = useCallback(async () => {
    if (reactFlowWrapper.current) {
      try {
        const canvas = await html2canvas(reactFlowWrapper.current)
        const link = document.createElement('a')
        link.download = `${mindMap.title.replace(/\s+/g, '-').toLowerCase()}.png`
        link.href = canvas.toDataURL()
        link.click()
      } catch (error) {
        console.error('Error exporting image:', error)
      }
    }
  }, [mindMap.title])

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen)
  }, [isFullscreen])

  // Registra i tipi di nodi personalizzati
  const nodeTypes = {
    custom: SimpleMindMapNodeComponent,
  }

  // Converte i nodi per ReactFlow
  const reactFlowNodes = nodes.map(node => ({
    ...node,
    type: 'custom',
    data: {
      ...node.data,
      type: node.type
    }
  }))

  return (
    <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50' : 'h-96'} ${className}`}>
      <ReactFlowProvider>
        <div className={`w-full h-full ${isFullscreen ? '' : 'border border-gray-200 rounded-lg bg-white'}`}>
          <div ref={reactFlowWrapper} className="relative w-full h-full">
            <ReactFlow
              nodes={reactFlowNodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              connectionMode={ConnectionMode.Loose}
              fitView
              attributionPosition="bottom-left"
              nodesDraggable={!readOnly && enableEditing}
              nodesConnectable={!readOnly && enableEditing}
              elementsSelectable={true}
              selectNodesOnDrag={!readOnly}
              panOnDrag={enableEditing}
              zoomOnScroll={enableEditing}
              zoomOnPinch={enableEditing}
              minZoom={0.1}
              maxZoom={2}
            >
              <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
            </ReactFlow>
          </div>

          <Panel position="top-right" className="flex items-center space-x-2">
            <button
              onClick={exportImage}
              className="p-2 bg-white rounded-lg shadow-sm border border-gray-200 hover:bg-gray-50 transition-colors"
              title="Esporta come immagine"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={toggleFullscreen}
              className="p-2 bg-white rounded-lg shadow-sm border border-gray-200 hover:bg-gray-50 transition-colors"
              title={isFullscreen ? "Esci da schermo intero" : "Schermo intero"}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </Panel>

          <Panel position="bottom-left" className="bg-white rounded-lg shadow-sm border border-gray-200 p-2">
            <div className="text-xs text-gray-600">
              <div className="font-semibold mb-1">{mindMap.title}</div>
              <div>Nodi: {mindMap.nodes.length} | Connessioni: {mindMap.edges.length}</div>
            </div>
          </Panel>
        </div>
      </ReactFlowProvider>
    </div>
  )
}

export default SimpleMindMapViewer