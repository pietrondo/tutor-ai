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

// Custom node component per il test visivo
const TestMindMapNodeComponent = ({ data, selected }: { data: any; selected: boolean }) => {
  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'central': return <Brain className="w-5 h-5 text-white" />
      case 'topic': return <BookOpen className="w-4 h-4 text-white" />
      case 'subtopic': return <Target className="w-3 h-3 text-white" />
      case 'example': return <Lightbulb className="w-3 h-3 text-white" />
      case 'connection': return <Zap className="w-3 h-3 text-white" />
      default: return <Circle className="w-4 h-4 text-white" />
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
    <div className={`p-4 min-w-[150px] max-w-[300px] ${selected ? 'ring-2 ring-blue-400 ring-offset-2' : ''} ${getNodeShape(data.type)} ${getNodeColor(data.type, data.importance)} text-white shadow-lg transition-all duration-200 hover:shadow-xl`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">
          {getNodeIcon(data.type)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-sm text-white line-clamp-2">
            {data.label}
          </div>
          {data.description && (
            <div className="text-xs text-white/90 mt-1 line-clamp-2">
              {data.description}
            </div>
          )}
          {data.topics && data.topics.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {data.topics.slice(0, 3).map((topic: string, index: number) => (
                <span key={index} className="text-xs bg-white/20 px-2 py-1 rounded-full">
                  {topic}
                </span>
              ))}
              {data.topics.length > 3 && (
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full">
                  +{data.topics.length - 3}
                </span>
              )}
            </div>
          )}
          {data.examples && data.examples.length > 0 && (
            <div className="mt-2 text-xs text-white/80">
              <div className="font-semibold mb-1">Esempi:</div>
              <div className="flex flex-wrap gap-1">
                {data.examples.slice(0, 2).map((example: string, index: number) => (
                  <span key={index} className="bg-white/10 px-1 py-0.5 rounded text-xs">
                    {example}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Dati di test ricchi e variegati
const testNodes: Node[] = [
  {
    id: 'central',
    type: 'custom',
    position: { x: 400, y: 300 },
    data: {
      label: 'Intelligenza Artificiale',
      description: 'Concetti fondamentali e applicazioni',
      type: 'central',
      importance: 'high'
    }
  },
  {
    id: 'machine-learning',
    type: 'custom',
    position: { x: 200, y: 150 },
    data: {
      label: 'Machine Learning',
      description: 'Algoritmi che imparano dai dati',
      type: 'topic',
      importance: 'high',
      topics: ['Deep Learning', 'Neural Networks', 'Reinforcement Learning']
    }
  },
  {
    id: 'nlp',
    type: 'custom',
    position: { x: 600, y: 150 },
    data: {
      label: 'NLP',
      description: 'Elaborazione del linguaggio naturale',
      type: 'topic',
      importance: 'high',
      topics: ['Transformer', 'BERT', 'GPT']
    }
  },
  {
    id: 'computer-vision',
    type: 'custom',
    position: { x: 200, y: 450 },
    data: {
      label: 'Computer Vision',
      description: 'Visione artificiale',
      type: 'topic',
      importance: 'medium',
      topics: ['Image Recognition', 'Object Detection']
    }
  },
  {
    id: 'ethics',
    type: 'custom',
    position: { x: 600, y: 450 },
    data: {
      label: 'AI Ethics',
      description: 'Considerazioni etiche sull\'IA',
      type: 'topic',
      importance: 'high',
      topics: ['Bias', 'Privacy', 'Accountability']
    }
  },
  {
    id: 'neural-networks',
    type: 'custom',
    position: { x: 50, y: 50 },
    data: {
      label: 'Neural Networks',
      description: 'Reti neurali artificiali',
      type: 'subtopic',
      importance: 'medium',
      examples: ['CNN', 'RNN', 'LSTM']
    }
  },
  {
    id: 'transformers',
    type: 'custom',
    position: { x: 750, y: 50 },
    data: {
      label: 'Transformers',
      description: 'Architettura transformer',
      type: 'subtopic',
      importance: 'high',
      examples: ['Attention', 'Self-Attention']
    }
  },
  {
    id: 'cnn-example',
    type: 'custom',
    position: { x: 50, y: 350 },
    data: {
      label: 'CNN Example',
      description: 'Rete neurale convoluzionale',
      type: 'example',
      importance: 'low',
      examples: ['Image Classification', 'Feature Extraction']
    }
  },
  {
    id: 'bias-example',
    type: 'custom',
    position: { x: 750, y: 350 },
    data: {
      label: 'Algorithmic Bias',
      description: 'Bias negli algoritmi',
      type: 'example',
      importance: 'medium',
      examples: ['Training Data Bias', 'Model Bias']
    }
  }
]

const testEdges: Edge[] = [
  {
    id: 'edge-ml',
    source: 'central',
    target: 'machine-learning',
    type: 'smoothstep',
    animated: true
  },
  {
    id: 'edge-nlp',
    source: 'central',
    target: 'nlp',
    type: 'smoothstep',
    animated: true
  },
  {
    id: 'edge-cv',
    source: 'central',
    target: 'computer-vision',
    type: 'smoothstep',
    animated: true
  },
  {
    id: 'edge-ethics',
    source: 'central',
    target: 'ethics',
    type: 'smoothstep',
    animated: true
  },
  {
    id: 'edge-nn',
    source: 'machine-learning',
    target: 'neural-networks',
    type: 'smoothstep'
  },
  {
    id: 'edge-transformers',
    source: 'nlp',
    target: 'transformers',
    type: 'smoothstep'
  },
  {
    id: 'edge-cnn',
    source: 'computer-vision',
    target: 'cnn-example',
    type: 'smoothstep'
  },
  {
    id: 'edge-bias',
    source: 'ethics',
    target: 'bias-example',
    type: 'smoothstep'
  }
]

// Componente principale del test
const TestVisualMindMap: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(testNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(testEdges)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const exportImage = useCallback(async () => {
    if (reactFlowWrapper.current) {
      try {
        const canvas = await html2canvas(reactFlowWrapper.current, {
          backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
          scale: 2
        })
        const link = document.createElement('a')
        link.download = `mindmap-test-${Date.now()}.png`
        link.href = canvas.toDataURL()
        link.click()
      } catch (error) {
        console.error('Error exporting image:', error)
      }
    }
  }, [theme])

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen)
  }, [isFullscreen])

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }, [theme])

  // Registra i tipi di nodi personalizzati
  const nodeTypes = {
    custom: TestMindMapNodeComponent,
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <ReactFlowProvider>
        <div className={`w-full h-screen ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
          <div ref={reactFlowWrapper} className="relative w-full h-full">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              connectionMode={ConnectionMode.Loose}
              fitView
              attributionPosition="bottom-left"
              nodesDraggable={true}
              nodesConnectable={false}
              elementsSelectable={true}
              selectNodesOnDrag={false}
              panOnDrag={true}
              zoomOnScroll={true}
              zoomOnPinch={true}
              minZoom={0.1}
              maxZoom={2}
              defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
            >
              <Background
                variant={BackgroundVariant.Dots}
                gap={20}
                size={1}
                color={theme === 'dark' ? '#374151' : '#e5e7eb'}
              />
            </ReactFlow>
          </div>

          <Panel position="top-right" className="flex items-center space-x-2">
            <button
              onClick={exportImage}
              className="p-3 bg-blue-500 text-white rounded-lg shadow-sm hover:bg-blue-600 transition-colors"
              title="Esporta come immagine"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={toggleTheme}
              className="p-3 bg-purple-500 text-white rounded-lg shadow-sm hover:bg-purple-600 transition-colors"
              title="Cambia tema"
            >
              {theme === 'light' ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>
            <button
              onClick={toggleFullscreen}
              className="p-3 bg-green-500 text-white rounded-lg shadow-sm hover:bg-green-600 transition-colors"
              title={isFullscreen ? "Esci da schermo intero" : "Schermo intero"}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </Panel>

          <Panel position="top-left" className={`${theme === 'dark' ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'} rounded-lg shadow-sm border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} p-4`}>
            <div className="text-sm">
              <div className="font-bold text-lg mb-2">Test Visivo MindMap</div>
              <div className="space-y-1">
                <div><strong>Nodi:</strong> {nodes.length}</div>
                <div><strong>Connessioni:</strong> {edges.length}</div>
                <div><strong>Tema:</strong> {theme}</div>
              </div>
              <div className="mt-3 text-xs opacity-75">
                Test per screenshot e analisi grafica
              </div>
            </div>
          </Panel>

          <Panel position="bottom-left" className={`${theme === 'dark' ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'} rounded-lg shadow-sm border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} p-3 max-w-sm`}>
            <div className="text-xs space-y-1">
              <div className="font-semibold mb-1">Istruzioni per il test:</div>
              <div>• Trascina i nodi per riposizionarli</div>
              <div>• Usa la rotellina del mouse per zoomare</div>
              <div>• Clicca sul pulsante di download per salvare screenshot</div>
              <div>• Cambia tema per testare modalità chiara/scura</div>
              <div>• Verifica colori, contrasti e leggibilità</div>
            </div>
          </Panel>
        </div>
      </ReactFlowProvider>
    </div>
  )
}

export default TestVisualMindMap