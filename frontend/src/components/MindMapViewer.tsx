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
import { MindMap, MindMapNode, MindMapEdge } from '@/types/mindmap'
import 'reactflow/dist/style.css'

// Custom node components
const MindMapNodeComponent = ({ data, selected }: { data: MindMapNode['data'] & { type: string }; selected: boolean }) => {
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
              {data.topics.slice(0, 2).map((topic, index) => (
                <span key={index} className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                  {topic}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface MindMapViewerProps {
  mindMap: MindMap
  onMindMapChange?: (mindMap: MindMap) => void
  readOnly?: boolean
  enableEditing?: boolean
  className?: string
}

export function MindMapViewer({
  mindMap,
  onMindMapChange,
  readOnly = false,
  enableEditing = true,
  className = ''
}: MindMapViewerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(mindMap.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(mindMap.edges)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const nodeTypes = React.useMemo(() => ({
    mindmap: MindMapNodeComponent,
  }), [])

  const onConnect = useCallback(
    (params: any) => {
      if (params.source === params.target) return false

      const newEdge: MindMapEdge = {
        id: `${params.source}-${params.target}`,
        source: params.source,
        target: params.target,
        type: 'connection',
        data: {
          relationship: 'connected_to'
        },
        style: {
          stroke: '#94a3b8',
          strokeWidth: 2
        }
      }

      setEdges((eds) => addEdge(newEdge, eds))
      return true
    },
    []
  )

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id)
  }, [])

  const exportMindMap = useCallback(async (format: 'json' | 'image') => {
    if (format === 'json') {
      const exportData = {
        ...mindMap,
        nodes,
        edges,
        exportedAt: new Date().toISOString()
      }

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mindmap-${mindMap.title}-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    } else if (format === 'image') {
      try {
        if (reactFlowWrapper.current) {
          const canvas = await html2canvas(reactFlowWrapper.current, {
            backgroundColor: mindMap.style.theme === 'dark' ? '#1f2937' : '#ffffff',
            scale: 2
          })

          const url = canvas.toDataURL('image/png')
          const a = document.createElement('a')
          a.href = url
          a.download = `mindmap-${mindMap.title}-${Date.now()}.png`
          a.click()
        }
      } catch (error) {
        console.error('Error exporting image:', error)
      }
    }
  }, [mindMap, nodes, edges])

  const saveMindMap = useCallback(() => {
    const updatedMindMap: MindMap = {
      ...mindMap,
      nodes: nodes as MindMapNode[],
      edges: edges as MindMapEdge[],
      metadata: {
        ...mindMap.metadata,
        updatedAt: new Date().toISOString()
      }
    }

    // Save to localStorage
    const savedMaps = JSON.parse(localStorage.getItem('mindmaps') || '[]')
    const existingIndex = savedMaps.findIndex((m: MindMap) => m.id === mindMap.id)

    if (existingIndex >= 0) {
      savedMaps[existingIndex] = updatedMindMap
    } else {
      savedMaps.push(updatedMindMap)
    }

    localStorage.setItem('mindmaps', JSON.stringify(savedMaps))
    onMindMapChange?.(updatedMindMap)
  }, [mindMap, nodes, edges, onMindMapChange])

  const generateMindMapWithAI = useCallback(async () => {
    setIsGenerating(true)
    try {
      // This would call your AI service to generate a mind map
      // For now, we'll create a simple example structure
      const centralNode: MindMapNode = {
        id: 'central',
        type: 'central',
        position: { x: 400, y: 300 },
        data: {
          label: mindMap.title || 'Concepto Principale',
          description: mindMap.description,
          color: '#3b82f6',
          fontSize: 16,
          importance: 'high'
        }
      }

      const topicNodes: MindMapNode[] = [
        {
          id: 'topic-1',
          type: 'topic',
          position: { x: 200, y: 200 },
          data: {
            label: 'Concetto 1',
            description: 'Descrizione del concetto 1',
            importance: 'high',
            topics: ['Sotto-argomento 1', 'Sotto-argomento 2']
          }
        },
        {
          id: 'topic-2',
          type: 'topic',
          position: { x: 600, y: 200 },
          data: {
            label: 'Concetto 2',
            description: 'Descrizione del concetto 2',
            importance: 'medium',
            topics: ['Sotto-argomento 3']
          }
        },
        {
          id: 'topic-3',
          type: 'topic',
          position: { x: 400, y: 100 },
          data: {
            label: 'Concetto 3',
            description: 'Descrizione del concetto 3',
            importance: 'low'
          }
        }
      ]

      const newEdges: MindMapEdge[] = [
        {
          id: 'central-topic-1',
          source: 'central',
          target: 'topic-1',
          type: 'hierarchy',
          data: { relationship: 'contains' }
        },
        {
          id: 'central-topic-2',
          source: 'central',
          target: 'topic-2',
          type: 'hierarchy',
          data: { relationship: 'contains' }
        },
        {
          id: 'central-topic-3',
          source: 'central',
          target: 'topic-3',
          type: 'hierarchy',
          data: { relationship: 'contains' }
        }
      ]

      setNodes([centralNode, ...topicNodes])
      setEdges(newEdges)
      saveMindMap()
    } catch (error) {
      console.error('Error generating mind map:', error)
    } finally {
      setIsGenerating(false)
    }
  }, [mindMap, saveMindMap, setNodes, setEdges])

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen)
  }, [isFullscreen])

  const addNode = useCallback(() => {
    const newNode: MindMapNode = {
      id: `node-${Date.now()}`,
      type: 'topic',
      position: {
        x: Math.random() * 600 + 100,
        y: Math.random() * 400 + 100
      },
      data: {
        label: 'Nuovo Concetto',
        description: 'Descrizione del nuovo concetto',
        importance: 'medium'
      }
    }

    setNodes((nodes) => [...nodes, newNode])
  }, [])

  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nodes) => nodes.filter((node) => node.id !== nodeId))
    setEdges((edges) => edges.filter((edge) =>
      edge.source !== nodeId && edge.target !== nodeId
    ))
  }, [])

  useEffect(() => {
    // Update mind map when nodes or edges change
    if (onMindMapChange) {
      const updatedMindMap: MindMap = {
        ...mindMap,
        nodes: nodes as MindMapNode[],
        edges: edges as MindMapEdge[]
      }
      onMindMapChange(updatedMindMap)
    }
  }, [nodes, edges, mindMap, onMindMapChange])

  return (
    <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50' : 'h-96'} ${className}`}>
      <ReactFlowProvider>
        <div className={`w-full h-full ${isFullscreen ? '' : 'border border-gray-200 rounded-lg bg-white'}`}>
          <div className="relative w-full h-full">
            <Controls
              className={showControls ? '' : 'opacity-0 pointer-events-none'}
            >
              <div className="flex items-center space-x-1 bg-white rounded-lg shadow-sm border border-gray-200 p-1">
                <button
                  onClick={generateMindMapWithAI}
                  disabled={isGenerating || readOnly}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50"
                  title="Genera con AI"
                >
                  {isGenerating ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Brain className="w-4 h-4" />
                  )}
                </button>

                {enableEditing && !readOnly && (
                  <>
                    <button
                      onClick={addNode}
                      className="p-2 text-green-600 hover:bg-green-50 rounded transition-colors"
                      title="Aggiungi nodo"
                    >
                      <Plus className="w-4 h-4" />
                    </button>

                    {selectedNode && (
                      <button
                        onClick={() => deleteNode(selectedNode)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Elimina nodo"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                    )}
                  </>
                )}

                <div className="h-4 w-px bg-gray-300"></div>

                <button
                  onClick={() => exportMindMap('json')}
                  className="p-2 text-gray-600 hover:bg-gray-50 rounded transition-colors"
                  title="Esporta JSON"
                >
                  <Download className="w-4 h-4" />
                </button>

                <button
                  onClick={() => exportMindMap('image')}
                  className="p-2 text-gray-600 hover:bg-gray-50 rounded transition-colors"
                  title="Esporta immagine"
                >
                  <Download className="w-4 h-4" />
                </button>

                <button
                  onClick={saveMindMap}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                  title="Salva"
                >
                  <Save className="w-4 h-4" />
                </button>

                <button
                  onClick={toggleFullscreen}
                  className="p-2 text-gray-600 hover:bg-gray-50 rounded transition-colors"
                  title={isFullscreen ? 'Esci da schermo intero' : 'Schermo intero'}
                >
                  {isFullscreen ? (
                    <Minimize2 className="w-4 h-4" />
                  ) : (
                    <Maximize2 className="w-4 h-4" />
                  )}
                </button>

                <button
                  onClick={() => setShowControls(!showControls)}
                  className="p-2 text-gray-600 hover:bg-gray-50 rounded transition-colors"
                  title="Mostra/nascondi controlli"
                >
                  <Settings className="w-4 h-4" />
                </button>
              </div>
            </Controls>

            <Panel position="top-right" className="text-xs bg-white/90 backdrop-blur-sm rounded-lg p-2 border border-gray-200">
              <div className="font-medium text-gray-700 mb-1">
                {mindMap.title}
              </div>
              <div className="space-y-1 text-gray-600">
                <div>Nodi: {nodes.length}</div>
                <div>Connessioni: {edges.length}</div>
                <div>Sessione: {mindMap.sessionId}</div>
              </div>
            </Panel>

            <ReactFlow
              ref={reactFlowWrapper}
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={readOnly ? undefined : onConnect}
              onNodeClick={readOnly ? undefined : onNodeClick}
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
        </div>
      </ReactFlowProvider>
    </div>
  )
}