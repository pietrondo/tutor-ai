'use client'

import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { RefreshCw, Save, Download, ZoomIn, ZoomOut, Move3D, Sparkles, Layout, Search, Undo, Redo } from 'lucide-react'
import toast from 'react-hot-toast'
import type { StudyMindmap, StudyMindmapNode } from '@/types/mindmap'

const ROOT_NODE_ID = 'mindmap-root'
type MindmapInput = StudyMindmap | (Record<string, unknown> & { mindmap?: StudyMindmap })

interface MindmapNode {
  id: string
  x: number
  y: number
  title: string
  subtitle?: string
  level: string
  expanded: boolean
  hidden?: boolean
  vx?: number
  vy?: number
  path: StudyMindmapNode[]
  source?: StudyMindmapNode
}

const createPlaceholderNode = (title: string): StudyMindmapNode => ({
  id: `placeholder-${title.toLowerCase().replace(/\s+/g, '-')}`,
  title,
  summary: '',
  ai_hint: '',
  study_actions: [],
  priority: null,
  references: [],
  children: []
})

interface Connection {
  from: string
  to: string
  hidden?: boolean
}

export interface MindmapData {
  nodes: Map<string, MindmapNode>
  connections: Connection[]
  scale: number
  offset: { x: number; y: number }
}

interface VisualMindmapProps {
  data?: MindmapInput | null
  onSave?: (data: MindmapData) => void
  onExport?: (data: MindmapData) => void
  editable?: boolean
  className?: string
  onExpandNode?: (path: StudyMindmapNode[], prompt?: string) => Promise<void>
  onRegenerate?: () => void
}

export default function VisualMindmap({
  data,
  onSave,
  onExport,
  editable = true,
  className = '',
  onExpandNode,
  onRegenerate
}: VisualMindmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const clickNodeRef = useRef<string | null>(null)
  const nodeClickStartRef = useRef<{ x: number; y: number } | null>(null)
  const nodeDragMovedRef = useRef(false)
  const autoLayoutAppliedRef = useRef<boolean>(false)
  const [mindmapData, setMindmapData] = useState<MindmapData | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [draggedNode, setDraggedNode] = useState<string | null>(null)
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 })
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 })
  const [stats, setStats] = useState({
    nodeCount: 0,
    connectionCount: 0,
    expandedCount: 0,
    zoomLevel: 100
  })
  const [expandingNodes, setExpandingNodes] = useState<Set<string>>(new Set())
  const [isPlaceholderData, setIsPlaceholderData] = useState(false)
  const [editingNode, setEditingNode] = useState<string | null>(null)
  const [editText, setEditText] = useState({ title: '', subtitle: '' })
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showExpandDialog, setShowExpandDialog] = useState(false)
  const [expandPrompt, setExpandPrompt] = useState('')
  const [expandingNodeId, setExpandingNodeId] = useState<string | null>(null)
  const [showExplanationDialog, setShowExplanationDialog] = useState(false)
  const [selectedExplanationNode, setSelectedExplanationNode] = useState<MindmapNode | null>(null)

  // Auto-layout state
  const [isAutoLayout, setIsAutoLayout] = useState(false)
  const [isLayoutAnimating, setIsLayoutAnimating] = useState(false)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<string[]>([])
  const [selectedSearchIndex, setSelectedSearchIndex] = useState(-1)

  // Undo/Redo state
  const [history, setHistory] = useState<MindmapData[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)

  // Animation state
  const animationRef = useRef<number | undefined>(undefined)
  const targetPositionsRef = useRef<Map<string, { x: number; y: number }>>(new Map())

  const truncateText = (value?: string, limit = 120): string | undefined => {
    if (!value) return undefined
    const trimmed = value.trim()
    if (trimmed.length <= limit) {
      return trimmed
    }
    return `${trimmed.slice(0, limit - 1)}…`
  }

  type MindmapWithNodes = Partial<StudyMindmap> & { nodes: StudyMindmapNode[] }

  const hasNodeArray = (value: unknown): value is MindmapWithNodes =>
    typeof value === 'object' && value !== null && Array.isArray((value as MindmapWithNodes).nodes)

  const getStructuredMindmap = (input: MindmapInput | null | undefined): StudyMindmap | null => {
    if (!input) return null

    if (hasNodeArray(input)) {
      return {
        title: input.title ?? 'Mappa concettuale',
        overview: input.overview,
        nodes: input.nodes,
        study_plan: input.study_plan ?? [],
        references: input.references ?? []
      }
    }

    if (
      typeof input === 'object' &&
      input !== null &&
      'mindmap' in input &&
      hasNodeArray((input as { mindmap?: unknown }).mindmap)
    ) {
      const inner = (input as { mindmap: MindmapWithNodes }).mindmap
      return {
        title: inner.title ?? 'Mappa concettuale',
        overview: inner.overview,
        nodes: inner.nodes,
        study_plan: inner.study_plan ?? [],
        references: inner.references ?? []
      }
    }

    return null
  }

  const dataSignature = useMemo(() => {
    if (!data) return 'null'
    try {
      return JSON.stringify(data)
    } catch (error) {
      console.warn('Failed to serialize mindmap data for signature:', error)
      return `${Date.now()}`
    }
  }, [data])

  // Initialize mindmap data - only recreate when data actually changes
  useEffect(() => {
    console.log('🔄 Initializing mindmap data...', {
      hasData: !!data,
      dataSignature: dataSignature.substring(0, 50) + '...',
      timestamp: new Date().toISOString()
    })

    if (data) {
      console.log('📊 Data provided, analyzing structure...')
      createMindmapFromData(data)
    } else {
      // Only create default mindmap if explicitly needed, otherwise keep null
      // This prevents showing placeholder maps when real data is expected
      console.log('📭 No data provided - keeping mindmap empty')
      setMindmapData(null)
    }
    setExpandingNodes(new Set())
    // Clear dimensions cache when data changes
    dimensionsCache.current.clear()
  }, [dataSignature]) // Only depend on dataSignature, not both data and dataSignature

  // Force refresh when external mindmap data changes (detected via data content)
  useEffect(() => {
    if (!data) return

    const structured = getStructuredMindmap(data)
    if (!structured || !mindmapData) return

    // Count nodes in current visual data
    const currentVisualNodeCount = mindmapData.nodes.size

    // Count nodes in structured data (recursive)
    const countNodesInStructured = (nodes: StudyMindmapNode[]): number => {
      let count = nodes.length
      nodes.forEach(node => {
        if (node.children && node.children.length > 0) {
          count += countNodesInStructured(node.children)
        }
      })
      return count
    }

    const structuredNodeCount = countNodesInStructured(structured.nodes)

    console.log('🔍 Node count comparison:', {
      currentVisualNodeCount,
      structuredNodeCount,
      needsUpdate: currentVisualNodeCount !== structuredNodeCount,
      timestamp: new Date().toISOString()
    })

    // Log node IDs to identify missing ones
    const getStructuredNodeIds = (nodes: StudyMindmapNode[]): string[] => {
      let ids: string[] = []
      nodes.forEach(node => {
        if (node.id) ids.push(node.id)
        if (node.children && node.children.length > 0) {
          ids = ids.concat(getStructuredNodeIds(node.children))
        }
      })
      return ids
    }

    const structuredIds = getStructuredNodeIds(structured.nodes)
    const visualNodeIds = Array.from(mindmapData.nodes.values())
      .filter(node => node.source?.id)
      .map(node => node.source!.id)

    const missingIds = structuredIds.filter(id => !visualNodeIds.includes(id))
    const extraIds = visualNodeIds.filter(id => !structuredIds.includes(id))

    if (missingIds.length > 0 || extraIds.length > 0) {
      console.log('🔍 Node ID comparison:', {
        missingIds,
        extraIds,
        totalStructured: structuredIds.length,
        totalVisual: visualNodeIds.length
      })

      // Log any critical node mismatches for debugging
      if (missingIds.length > 0) {
        console.warn('⚠️ Nodes found in structured data but missing from visual mindmap:', missingIds)
      }
    }

    // If there's a mismatch, recreate the mindmap
    if (currentVisualNodeCount !== structuredNodeCount) {
      console.log('🔄 Recreating mindmap due to node count change')
      createMindmapFromData(data)
    }
  }, [dataSignature])

  // Additional effect to force update when external changes are detected
  useEffect(() => {
    if (!data || !mindmapData) return

    const structured = getStructuredMindmap(data)
    if (!structured) return

    // Check if any nodes have children that aren't reflected in the visual data
    const hasUnrenderedChildren = (structuredNode: StudyMindmapNode): boolean => {
      const visualNode = Array.from(mindmapData.nodes.values()).find(
        vn => vn.source && vn.source.id === structuredNode.id
      )

      if (!visualNode && structuredNode.children && structuredNode.children.length > 0) {
        console.warn('⚠️ Unrendered parent found:', {
          nodeId: structuredNode.id,
          nodeTitle: structuredNode.title?.substring(0, 50),
          childrenCount: structuredNode.children.length
        })
        return true
      }

      if (structuredNode.children && structuredNode.children.length > 0) {
        return structuredNode.children.some(hasUnrenderedChildren)
      }

      return false
    }

    const needsUpdate = structured.nodes.some(hasUnrenderedChildren)

    if (needsUpdate) {
      console.log('🔄 Recreating mindmap due to unrendered children')
      createMindmapFromData(data)
    }

    // Debug validation - ensure all structured nodes are properly rendered
    console.log('✅ Mindmap validation complete:', {
      totalStructuredNodes: structured.nodes.length,
      totalRenderedNodes: mindmapData.nodes.size,
      totalConnections: mindmapData.connections.length
    })
  }, [data, dataSignature, mindmapData?.nodes.size])

  const createDefaultMindmap = () => {
    const centerX = 800
    const centerY = 400

    const nodes = new Map<string, MindmapNode>()
    const connections: Connection[] = []

    const rootPlaceholder = createPlaceholderNode('Mappa Concettuale')
    nodes.set(ROOT_NODE_ID, {
      id: ROOT_NODE_ID,
      x: centerX,
      y: centerY,
      title: 'Mappa Concettuale',
      subtitle: 'Esempio - Genera mappa reale',
      level: 'main',
      expanded: true,
      path: [rootPlaceholder],
      source: rootPlaceholder
    })

    const level1Nodes = [
      { id: 'spedizioni', title: 'Spedizioni Principali', angle: 0 },
      { id: 'contratacion', title: 'Casa de la Contratacion', angle: 72 },
      { id: 'analogie', title: 'Analogie con Conrad', angle: 144 },
      { id: 'controversie', title: 'Controversie', angle: 216 },
      { id: 'eredita', title: 'Eredità Storica', angle: 288 }
    ]

    const radius1 = 200
    level1Nodes.forEach(node => {
      const angle = (node.angle * Math.PI) / 180
      const x = centerX + Math.cos(angle) * radius1
      const y = centerY + Math.sin(angle) * radius1

      const nodePlaceholder = createPlaceholderNode(node.title)
      nodes.set(node.id, {
        id: node.id,
        x,
        y,
        title: node.title,
        level: 'level-1',
        expanded: false,
        path: [rootPlaceholder, nodePlaceholder],
        source: nodePlaceholder
      })

      connections.push({ from: ROOT_NODE_ID, to: node.id })
    })

    setIsPlaceholderData(true)
    setMindmapData({
      nodes,
      connections,
      scale: 1,
      offset: { x: 0, y: 0 }
    })
  }

  const createMindmapFromData = (inputData: MindmapInput | null | undefined) => {
    console.log('🚀 Starting mindmap creation from data:', {
      hasInput: !!inputData,
      inputType: inputData ? (typeof inputData) : 'null',
      inputDataKeys: inputData ? Object.keys(inputData) : [],
      timestamp: new Date().toISOString()
    })

    // Detailed input logging
    if (inputData) {
      console.log('📋 Input data details:', {
        title: inputData.title,
        hasNodes: !!inputData.nodes,
        nodesLength: (inputData.nodes as any[])?.length || 0,
        firstNodeTitle: (inputData.nodes as any[])?.[0]?.title || 'No nodes',
        allNodeTitles: (inputData.nodes as any[])?.map((n: any) => n.title) || []
      })
    }

    const structured = getStructuredMindmap(inputData)
    if (!structured || !Array.isArray(structured.nodes) || structured.nodes.length === 0) {
      console.warn('⚠️ No valid structured data found, keeping canvas empty')
      console.log('🔍 Structured data check:', {
        structured: !!structured,
        isArray: Array.isArray(structured?.nodes),
        nodesLength: structured?.nodes?.length || 0
      })
      setIsPlaceholderData(false)
      setMindmapData(null)
      return
    }

    console.log('📊 Structured data extracted:', {
      title: structured.title,
      nodeCount: structured.nodes.length,
      hasOverview: !!structured.overview,
      studyPlanLength: structured.study_plan?.length || 0,
      referencesCount: structured.references?.length || 0
    })

    setIsPlaceholderData(false)

    const centerX = 800
    const centerY = 400
    const baseRadius = 220
    const levelSpacing = 150

    const nodes = new Map<string, MindmapNode>()
    const connections: Connection[] = []
    const singleRootNode = structured.nodes.length === 1 ? structured.nodes[0] : null
    const rootTitle =
      singleRootNode?.title?.trim() ||
      structured.title?.trim() ||
      'Mappa concettuale'
    const rootSubtitle = truncateText(
      singleRootNode?.summary || structured.overview,
      140
    )

    console.log('🎯 Root node configuration:', {
      title: rootTitle,
      hasSingleRoot: !!singleRootNode,
      rootId: singleRootNode?.id,
      rootChildrenCount: singleRootNode?.children?.length || 0
    })

    const rootNodeSource = singleRootNode ?? createPlaceholderNode(rootTitle)
    nodes.set(ROOT_NODE_ID, {
      id: ROOT_NODE_ID,
      x: centerX,
      y: centerY,
      title: rootTitle,
      subtitle: rootSubtitle,
      level: 'main',
      expanded: true,
      path: [rootNodeSource],
      source: rootNodeSource
    })

    const usedIds = new Set<string>([ROOT_NODE_ID])
    let syntheticIndex = 0

    const getNodeId = (candidate?: string): string => {
      let base = candidate && candidate.trim().length > 0 ? candidate : `node-${syntheticIndex++}`
      let unique = base
      while (usedIds.has(unique)) {
        unique = `${base}-${syntheticIndex++}`
      }
      usedIds.add(unique)
      return unique
    }

    // Log per tracciare i nodi processati
    const processedNodeIds = new Set<string>()
    const nodeProcessingLog: Array<{id: string, originalId: string, title: string, level: string, children: number}> = []

    const placeChildren = (
      children: StudyMindmapNode[],
      parentId: string,
      depth: number,
      parentAngle: number,
      parentPath: StudyMindmapNode[]
    ) => {
      console.log(`📍 Processing ${children.length} children for parent ${parentId} at depth ${depth}`)

      if (!children.length) return
      const radius = baseRadius + depth * levelSpacing
      const count = children.length
      const angleStep =
        parentId === ROOT_NODE_ID ? (Math.PI * 2) / count : Math.PI / Math.max(count, 2)

      children.forEach((child, index) => {
        // Log di debugging per ogni nodo processato
        if (child.id) {
          processedNodeIds.add(child.id)
        }

        const angle =
          parentId === ROOT_NODE_ID
            ? index * angleStep
            : parentAngle + (index - (count - 1) / 2) * angleStep

        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius

        const nodeId = getNodeId(child.id)
        const nodePath = [...parentPath, child]

        // Log per ogni nodo creato
        const nodeInfo = {
          id: nodeId,
          originalId: child.id,
          title: child.title?.substring(0, 50) + (child.title?.length > 50 ? '...' : ''),
          level: `level-${depth + 1}`,
          children: child.children?.length || 0
        }
        nodeProcessingLog.push(nodeInfo)

        nodes.set(nodeId, {
          id: nodeId,
          x,
          y,
          title: child.title || `Nodo ${index + 1}`,
          subtitle: truncateText(child.summary, 90),
          level: `level-${depth + 1}`,
          expanded: Boolean(child.children && child.children.length > 0),
          path: nodePath,
          source: child
        })

        connections.push({ from: parentId, to: nodeId })

        if (child.children && child.children.length > 0) {
          placeChildren(child.children, nodeId, depth + 1, angle, nodePath)
        }
      })
    }

    const rootChildren = singleRootNode?.children && singleRootNode.children.length > 0
      ? singleRootNode.children
      : structured.nodes

    console.log('🌳 Root children configuration:', {
      isSingleRoot: !!singleRootNode,
      rootChildrenCount: rootChildren.length,
      childrenIds: rootChildren.map(c => ({ id: c.id, title: c.title?.substring(0, 30) }))
    })

    const initialPath = singleRootNode ? [singleRootNode] : []

    placeChildren(rootChildren, ROOT_NODE_ID, 0, 0, initialPath)

    console.log('🎯 Mindmap creation completed:', {
      totalNodes: nodes.size,
      totalConnections: connections.length,
      totalProcessedIds: processedNodeIds.size
    })

    console.log('📋 Detailed node processing log:', nodeProcessingLog)
    console.log(`✅ Successfully processed ${nodeProcessingLog.length} nodes`)

    setMindmapData({
      nodes,
      connections,
      scale: 1,
      offset: { x: 0, y: 0 }
    })
  }

  // Resize canvas
  useEffect(() => {
    const resizeCanvas = () => {
      if (canvasRef.current && containerRef.current) {
        canvasRef.current.width = containerRef.current.clientWidth
        canvasRef.current.height = containerRef.current.clientHeight
        render()
      }
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    return () => window.removeEventListener('resize', resizeCanvas)
  }, [mindmapData])

  // Setup event listeners
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const handleMouseDown = (e: MouseEvent) => {
      if (!mindmapData) return
      const rect = canvas.getBoundingClientRect()
      const x = (e.clientX - rect.left - mindmapData.offset.x) / mindmapData.scale
      const y = (e.clientY - rect.top - mindmapData.offset.y) / mindmapData.scale

      // Check if clicking on a node
      for (const [id, node] of mindmapData.nodes) {
        if (!node.hidden && isPointInNode(x, y, node)) {
          // Check se il nodo ha una spiegazione dettagliata
          const explanation = getNodeExplanation(node)
          if (explanation && e.shiftKey) {
            // Shift+click per mostrare spiegazione
            setSelectedExplanationNode(node)
            setShowExplanationDialog(true)
            return
          }

          setDraggedNode(id)
          setMouseOffset({ x: x - node.x, y: y - node.y })
          clickNodeRef.current = id
          nodeClickStartRef.current = { x: e.clientX, y: e.clientY }
          nodeDragMovedRef.current = false
          return
        }
      }

      // Otherwise start panning
      setIsDragging(true)
      setLastMousePos({ x: e.clientX, y: e.clientY })
      canvas.style.cursor = 'grabbing'
      clickNodeRef.current = null
      nodeClickStartRef.current = null
      nodeDragMovedRef.current = false
    }

    const handleDoubleClick = (e: MouseEvent) => {
      if (!mindmapData || !editable) return
      const rect = canvas.getBoundingClientRect()
      const x = (e.clientX - rect.left - mindmapData.offset.x) / mindmapData.scale
      const y = (e.clientY - rect.top - mindmapData.offset.y) / mindmapData.scale

      // Check if double-clicking on a node
      for (const [id, node] of mindmapData.nodes) {
        if (!node.hidden && isPointInNode(x, y, node)) {
          setEditingNode(id)
          setEditText({
            title: node.title,
            subtitle: node.subtitle || ''
          })
          setShowEditDialog(true)
          return
        }
      }
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (!mindmapData) return
      const rect = canvas.getBoundingClientRect()

      if (draggedNode) {
        const x = (e.clientX - rect.left - mindmapData.offset.x) / mindmapData.scale
        const y = (e.clientY - rect.top - mindmapData.offset.y) / mindmapData.scale

        const node = mindmapData.nodes.get(draggedNode)
        if (node) {
          if (nodeClickStartRef.current) {
            const moveDistance = Math.hypot(
              e.clientX - nodeClickStartRef.current.x,
              e.clientY - nodeClickStartRef.current.y
            )
            if (moveDistance > 5) {
              nodeDragMovedRef.current = true
            }
          }
          node.x = x - mouseOffset.x
          node.y = y - mouseOffset.y
          render()
        }
      } else if (isDragging) {
        const dx = e.clientX - lastMousePos.x
        const dy = e.clientY - lastMousePos.y

        setMindmapData(prev => ({
          ...prev,
          offset: {
            x: prev.offset.x + dx,
            y: prev.offset.y + dy
          }
        }))

        setLastMousePos({ x: e.clientX, y: e.clientY })
        render()
      }
    }

    const handleMouseUp = () => {
      const clickedNodeId = clickNodeRef.current
      const moved = nodeDragMovedRef.current

      setDraggedNode(null)
      setIsDragging(false)
      if (canvas) {
        canvas.style.cursor = 'grab'
      }

      if (clickedNodeId && !moved) {
        toggleNodeExpansion(clickedNodeId)
      }

      clickNodeRef.current = null
      nodeClickStartRef.current = null
      nodeDragMovedRef.current = false
    }

    const handleWheel = (e: WheelEvent) => {
      if (!mindmapData) return
      e.preventDefault()

      const delta = e.deltaY > 0 ? 0.9 : 1.1
      const newScale = Math.max(0.5, Math.min(3, mindmapData.scale * delta))

      setMindmapData(prev => ({
        ...prev,
        scale: newScale
      }))
    }

    canvas.addEventListener('mousedown', handleMouseDown)
    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseup', handleMouseUp)
    canvas.addEventListener('wheel', handleWheel)
    canvas.addEventListener('dblclick', handleDoubleClick)
    canvas.style.cursor = 'grab'

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown)
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseup', handleMouseUp)
      canvas.removeEventListener('wheel', handleWheel)
      canvas.removeEventListener('dblclick', handleDoubleClick)
    }
  }, [mindmapData, draggedNode, mouseOffset, lastMousePos, isDragging])

  useEffect(() => {
    if (!mindmapData) return

    const visibleNodes = Array.from(mindmapData.nodes.values()).filter(node => !node.hidden)
    const visibleConnections = mindmapData.connections.filter(conn => {
      const fromNode = mindmapData.nodes.get(conn.from)
      const toNode = mindmapData.nodes.get(conn.to)
      return fromNode && toNode && !toNode.hidden
    })
    const expandedNodes = visibleNodes.filter(node => node.expanded)

    setStats({
      nodeCount: visibleNodes.length,
      connectionCount: visibleConnections.length,
      expandedCount: expandedNodes.length,
      zoomLevel: Math.round(mindmapData.scale * 100)
    })
  }, [mindmapData])

  // Auto layout once when data becomes available
  useEffect(() => {
    if (mindmapData && mindmapData.nodes.size > 0 && !autoLayoutAppliedRef.current) {
      try {
        performAutoLayout()
        handleZoomToFit()
        autoLayoutAppliedRef.current = true
      } catch (e) {
        console.warn('Auto layout failed:', e)
      }
    }
  }, [mindmapData])

  // Render function
  const render = () => {
    if (!canvasRef.current || !mindmapData) return

    const ctx = canvasRef.current.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height)

    ctx.save()
    ctx.translate(mindmapData.offset.x, mindmapData.offset.y)
    ctx.scale(mindmapData.scale, mindmapData.scale)

    // Draw connections
    mindmapData.connections.forEach(conn => {
      const fromNode = mindmapData.nodes.get(conn.from)
      const toNode = mindmapData.nodes.get(conn.to)

      if (fromNode && toNode && !toNode.hidden) {
        drawConnection(ctx, fromNode, toNode)
      }
    })

    // Draw nodes
    mindmapData.nodes.forEach(node => {
      if (!node.hidden) {
        drawNode(ctx, node)
      }
    })

    ctx.restore()
  }

  useEffect(() => {
    render()
  }, [mindmapData, expandingNodes])

  // Memoization cache for node dimensions
  const dimensionsCache = useRef(new Map<string, { width: number; height: number }>())

  // Funzione per estrarre informazioni sul riferimento sorgente
  const extractSourceInfo = (title: string, source?: StudyMindmapNode): { cleanTitle: string; sourceRef?: string } => {
    if (!title || typeof title !== 'string') return { cleanTitle: 'Nodo' }

    let cleanTitle = title
    let sourceRef: string | undefined

    // Estrai informazioni sulla fonte (page: X, pos: Y)
    const pagePosMatch = title.match(/(?:page:\s*(\d+))?\s*,?\s*(?:pos:\s*(\d+))?/i)
    if (pagePosMatch && (pagePosMatch[1] || pagePosMatch[2])) {
      const page = pagePosMatch[1] ? `pag.${pagePosMatch[1]}` : ''
      const pos = pagePosMatch[2] ? `pos.${pagePosMatch[2]}` : ''
      sourceRef = [page, pos].filter(Boolean).join(', ')
    }

    // Estrai riferimenti tra parentesi quadre [libro: ...]
    const bracketMatch = title.match(/\[([^\]]+)\]/)
    if (bracketMatch && !sourceRef) {
      sourceRef = bracketMatch[1]
    }

    // Estrai riferimenti da "tratto da:" o "estratto da:"
    const extractedMatch = title.match(/(?:tratto\s+da|estratto\s+da)\s*:\s*([^\n]+)/i)
    if (extractedMatch && !sourceRef) {
      sourceRef = extractedMatch[1].trim()
    }

    // NEW: Estrai URL e link web
    const urlMatch = title.match(/https?:\/\/[^\s)]+/gi)
    if (urlMatch && !sourceRef) {
      sourceRef = 'Fonte web'
    }

    // Pulizia più aggressiva del titolo rimuovendo tutti i riferimenti
    let cleaned = title
      // Rimuovi riferimenti a pagine e posizioni
      .replace(/\(?\s*page:\s*\d+\s*,\s*pos:\s*\d+\s*\)?/gi, '')
      .replace(/page\s*:\s*\d+/gi, '')
      .replace(/pos:\s*\d+/gi, '')
      // Rimuovi riferimenti tra parentesi quadre
      .replace(/\[.*?\]/g, '')
      // Rimuovi URL e link
      .replace(/https?:\/\/[^\s)]+/gi, '')
      // Rimuovi riferimenti a documenti e posizioni
      .replace(/\(.*?posizione.*?\)/gi, '')
      .replace(/\(.*?documento.*?\)/gi, '')
      // Rimuovi "tratto da" e "estratto da"
      .replace(/tratto\s+da\s*:\s*.*/gi, '')
      .replace(/estratto\s+da\s*:\s*.*/gi, '')
      // Rimuovi riferimenti a file o documenti
      .replace(/\b(file|documento|pdf)\s*[:-]?\s*[^\n]*/gi, '')
      // Rimuovi ID numerici lunghi (probabilmente ID documento)
      .replace(/\b[a-f0-9]{20,}\b/g, '')
      // Rimuovi testo che sembra essere un riferimento tecnico
      .replace(/\b(doc|ref|source)\s*[:-]?\s*[^\n]*/gi, '')

    cleaned = cleaned.trim()
    // Rimuovi spazi multipli e caratteri strani rimanenti
    cleaned = cleaned.replace(/\s+/g, ' ')
    cleaned = cleaned.replace(/^[,\s:;-]+|[,\s:;-]+$/g, '') // Rimuovi punteggiatura agli estremi

    // Se dopo la pulizia il titolo è troppo corto o vuoto, genera un titolo semanticamente corretto
    if (cleaned.length < 3) {
      if (source?.title && source.title.length > 3) {
        // Usa il titolo del nodo sorgente se disponibile
        cleaned = source.title
      } else if (title.includes('Caboto')) {
        cleaned = 'Viaggi di Esplorazione'
      } else if (title.toLowerCase().includes('sebastiano')) {
        cleaned = 'Figure Storiche'
      } else {
        cleaned = 'Concetto Principale'
      }
    }

    // Se il testo è troppo lungo, troncalo intelligentemente
    if (cleaned.length > 60) {
      const sentences = cleaned.split(/[.!?]/)
      if (sentences.length > 0) {
        cleaned = sentences[0].trim()
        if (!cleaned.endsWith('.') && cleaned.length > 60) {
          const lastSpace = cleaned.lastIndexOf(' ', 55)
          if (lastSpace > 30) {
            cleaned = cleaned.substring(0, lastSpace) + '...'
          }
        }
      }
    }

    return {
      cleanTitle: cleaned || title.substring(0, 45) + (title.length > 45 ? '...' : ''),
      sourceRef: sourceRef?.trim()
    }
  }

  // Funzione legacy per compatibilità
  const cleanNodeTitle = (title: string): string => {
    return extractSourceInfo(title).cleanTitle
  }

  // Funzione per ottenere la spiegazione dettagliata dal nodo
  const getNodeExplanation = (node: MindmapNode): string | null => {
    if (node.subtitle && node.subtitle.trim()) {
      return node.subtitle.trim()
    }

    // Se non c'è subtitle, prova a estrarre spiegazioni dal title originale
    if (node.source && node.source.summary) {
      return node.source.summary.trim()
    }

    return null
  }

  // Auto-layout algorithm
  const performAutoLayout = useCallback(() => {
    if (!mindmapData || isLayoutAnimating) return

    setIsLayoutAnimating(true)

    const nodes = Array.from(mindmapData.nodes.values()).filter(node => !node.hidden)
    const connections = mindmapData.connections.filter(conn => {
      const fromNode = mindmapData.nodes.get(conn.from)
      const toNode = mindmapData.nodes.get(conn.to)
      return fromNode && toNode && !fromNode.hidden && !toNode.hidden
    })

    // Force-directed layout parameters
    const ITERATIONS = 100
    const REPULSION_STRENGTH = 8000
    const ATTRACTION_STRENGTH = 0.1
    const IDEAL_DISTANCE = 200
    const DAMPING = 0.9
    const CENTER_FORCE = 0.01

    // Initialize forces
    const forces = new Map<string, { fx: number; fy: number }>()
    nodes.forEach(node => {
      forces.set(node.id, { fx: 0, fy: 0 })
    })

    // Simulate forces
    for (let iteration = 0; iteration < ITERATIONS; iteration++) {
      // Reset forces
      forces.forEach(force => {
        force.fx = 0
        force.fy = 0
      })

      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const nodeA = nodes[i]
          const nodeB = nodes[j]
          const dx = nodeB.x - nodeA.x
          const dy = nodeB.y - nodeA.y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance > 0) {
            const force = REPULSION_STRENGTH / (distance * distance)
            const fx = (dx / distance) * force
            const fy = (dy / distance) * force

            const forceA = forces.get(nodeA.id)!
            const forceB = forces.get(nodeB.id)!
            forceA.fx -= fx
            forceA.fy -= fy
            forceB.fx += fx
            forceB.fy += fy
          }
        }
      }

      // Attraction between connected nodes
      connections.forEach(conn => {
        const fromNode = mindmapData.nodes.get(conn.from)
        const toNode = mindmapData.nodes.get(conn.to)

        if (fromNode && toNode) {
          const dx = toNode.x - fromNode.x
          const dy = toNode.y - fromNode.y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance > 0) {
            const force = (distance - IDEAL_DISTANCE) * ATTRACTION_STRENGTH
            const fx = (dx / distance) * force
            const fy = (dy / distance) * force

            const forceFrom = forces.get(fromNode.id)!
            const forceTo = forces.get(toNode.id)!
            forceFrom.fx += fx
            forceFrom.fy += fy
            forceTo.fx -= fx
            forceTo.fy -= fy
          }
        }
      })

      // Center force to keep nodes in viewport
      const centerX = 800
      const centerY = 400
      nodes.forEach(node => {
        const dx = centerX - node.x
        const dy = centerY - node.y
        const force = forces.get(node.id)!
        force.fx += dx * CENTER_FORCE
        force.fy += dy * CENTER_FORCE
      })

      // Apply forces with damping
      const newTargets = new Map<string, { x: number; y: number }>()
      nodes.forEach(node => {
        const force = forces.get(node.id)!
        const targetX = node.x + force.fx * DAMPING
        const targetY = node.y + force.fy * DAMPING
        newTargets.set(node.id, { x: targetX, y: targetY })
      })

      targetPositionsRef.current = newTargets
    }

    // Smooth animation to target positions
    const animateToPositions = () => {
      if (!mindmapData) return

      const ANIMATION_DURATION = 800
      const startTime = Date.now()
      const startPositions = new Map<string, { x: number; y: number }>()

      mindmapData.nodes.forEach((node, id) => {
        startPositions.set(id, { x: node.x, y: node.y })
      })

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / ANIMATION_DURATION, 1)
        const easeProgress = 1 - Math.pow(1 - progress, 3) // Ease-out cubic

        const updatedNodes = new Map(mindmapData.nodes)
        let allReached = true

        nodes.forEach(node => {
          const start = startPositions.get(node.id)!
          const target = targetPositionsRef.current.get(node.id)!

          const currentX = start.x + (target.x - start.x) * easeProgress
          const currentY = start.y + (target.y - start.y) * easeProgress

          const distance = Math.sqrt(
            Math.pow(target.x - currentX, 2) + Math.pow(target.y - currentY, 2)
          )

          if (distance > 0.5) {
            allReached = false
          }

          updatedNodes.set(node.id, { ...node, x: currentX, y: currentY })
        })

        setMindmapData(prev => prev ? { ...prev, nodes: updatedNodes } : prev)

        if (!allReached && progress < 1) {
          animationRef.current = requestAnimationFrame(animate)
        } else {
          setIsLayoutAnimating(false)
          targetPositionsRef.current.clear()
        }
      }

      animationRef.current = requestAnimationFrame(animate)
    }

    animateToPositions()
  }, [mindmapData, isLayoutAnimating])

  // Search functionality
  const performSearch = useCallback((query: string) => {
    if (!mindmapData || !query.trim()) {
      setSearchResults([])
      setSelectedSearchIndex(-1)
      return
    }

    const normalizedQuery = query.toLowerCase().trim()
    const results: string[] = []

    mindmapData.nodes.forEach((node, id) => {
      if (node.hidden) return

      const titleMatch = node.title.toLowerCase().includes(normalizedQuery)
      const subtitleMatch = node.subtitle?.toLowerCase().includes(normalizedQuery)

      if (titleMatch || subtitleMatch) {
        results.push(id)
      }
    })

    setSearchResults(results)
    setSelectedSearchIndex(results.length > 0 ? 0 : -1)

    if (results.length > 0) {
      toast.success(`Trovati ${results.length} risultati`, { icon: '🔍' })
    } else {
      toast.error('Nessun risultato trovato', { icon: '🔍' })
    }
  }, [mindmapData])

  const navigateToSearchResult = useCallback((index: number) => {
    if (!mindmapData || searchResults.length === 0) return

    const validIndex = Math.max(0, Math.min(index, searchResults.length - 1))
    const nodeId = searchResults[validIndex]

    if (nodeId) {
      setSelectedSearchIndex(validIndex)

      // Center view on the found node
      const node = mindmapData.nodes.get(nodeId)
      if (node && canvasRef.current) {
        const newOffsetX = canvasRef.current.width / 2 - node.x * mindmapData.scale
        const newOffsetY = canvasRef.current.height / 2 - node.y * mindmapData.scale

        setMindmapData(prev => prev ? {
          ...prev,
          offset: { x: newOffsetX, y: newOffsetY }
        } : prev)
      }
    }
  }, [mindmapData, searchResults])

  // History management
  const saveToHistory = useCallback((data: MindmapData) => {
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push(JSON.parse(JSON.stringify(data))) // Deep clone

    // Limit history size to prevent memory issues
    if (newHistory.length > 50) {
      newHistory.shift()
    }

    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)
  }, [history, historyIndex])

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const previousState = history[historyIndex - 1]
      setMindmapData(previousState)
      setHistoryIndex(historyIndex - 1)
      toast.success('Annullato', { icon: '↶' })
    }
  }, [history, historyIndex])

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1]
      setMindmapData(nextState)
      setHistoryIndex(historyIndex + 1)
      toast.success('Ripristinato', { icon: '↷' })
    }
  }, [history, historyIndex])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Z: Undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault()
        undo()
      }
      // Ctrl/Cmd + Shift + Z or Ctrl/Cmd + Y: Redo
      else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault()
        redo()
      }
      // Ctrl/Cmd + F: Focus search
      else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault()
        // Focus search input
        const searchInput = document.getElementById('mindmap-search') as HTMLInputElement
        searchInput?.focus()
      }
      // F3: Next search result
      else if (e.key === 'F3' && !e.shiftKey) {
        e.preventDefault()
        navigateToSearchResult(selectedSearchIndex + 1)
      }
      // Shift + F3: Previous search result
      else if (e.key === 'F3' && e.shiftKey) {
        e.preventDefault()
        navigateToSearchResult(selectedSearchIndex - 1)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [undo, redo, navigateToSearchResult, selectedSearchIndex])

  const calculateNodeDimensions = (node: MindmapNode) => {
    // Extract source info for accurate dimension calculation
    const { cleanTitle, sourceRef } = extractSourceInfo(node.title, node.source)
    const hasSourceRef = sourceRef && sourceRef.length > 0

    const cacheKey = `${node.id}-${node.title}-${node.subtitle || ''}-${hasSourceRef}`
    if (dimensionsCache.current.has(cacheKey)) {
      return dimensionsCache.current.get(cacheKey)!
    }

    // Input validation
    const safeTitle = cleanTitle || 'Nodo'
    const safeSubtitle = node.subtitle?.trim() || ''

    // Get context with fallback
    const ctx = canvasRef.current?.getContext('2d')
    const hasValidContext = ctx && typeof ctx.measureText === 'function'

    const minWidth = 180
    const maxWidth = 320
    const padding = 20

    let titleWidth = 0
    let subtitleWidth = 0
    let sourceWidth = 0

    if (hasValidContext) {
      try {
        // Measure title
        ctx.font = 'bold 14px Inter, sans-serif'
        const titleMetrics = ctx.measureText(safeTitle)
        titleWidth = titleMetrics.width + padding * 2

        // Measure subtitle if present
        if (safeSubtitle) {
          ctx.font = '11px Inter, sans-serif'
          const subtitleMetrics = ctx.measureText(safeSubtitle)
          subtitleWidth = subtitleMetrics.width + padding * 2
        }

        // Measure source reference if present
        if (hasSourceRef) {
          ctx.font = '9px Inter, sans-serif'
          const sourceText = `📖 ${sourceRef}`
          const sourceMetrics = ctx.measureText(sourceText)
          sourceWidth = sourceMetrics.width + padding * 2
        }
      } catch (error) {
        console.warn('Error measuring text, using fallback estimation:', error)
      }
    }

    // Fallback estimation if context fails
    if (titleWidth === 0) {
      const avgCharWidth = 8 // Average width per character
      titleWidth = Math.max(safeTitle.length * avgCharWidth + padding * 2, minWidth)

      if (safeSubtitle) {
        subtitleWidth = Math.max(safeSubtitle.length * 6 + padding * 2, minWidth)
      }

      if (hasSourceRef) {
        sourceWidth = Math.max(sourceRef.length * 5 + padding * 2, minWidth)
      }
    }

    // Calculate final dimensions
    const width = Math.max(minWidth, Math.min(maxWidth, Math.max(titleWidth, subtitleWidth, sourceWidth)))

    // Calculate height based on content
    let height = 50 // Base height
    if (safeSubtitle) height += 20
    if (hasSourceRef) height += 20

    const dimensions = { width, height }
    dimensionsCache.current.set(cacheKey, dimensions)

    return dimensions
  }

  const isPointInNode = (x: number, y: number, node: MindmapNode): boolean => {
    const { width, height } = calculateNodeDimensions(node)

    return x >= node.x - width/2 && x <= node.x + width/2 &&
           y >= node.y - height/2 && y <= node.y + height/2
  }

  const drawNode = (ctx: CanvasRenderingContext2D, node: MindmapNode) => {
    const { width, height } = calculateNodeDimensions(node)
    const radius = 12

    // Check if this node is a search result
    const isSearchResult = searchResults.includes(node.id)
    const isSelectedResult = searchResults[selectedSearchIndex] === node.id

    // Extract source information
    const { cleanTitle, sourceRef } = extractSourceInfo(node.title, node.source)

    // Calculate if we need extra height for source reference
    const hasSourceRef = sourceRef && sourceRef.length > 0
    const extraHeight = hasSourceRef ? 20 : 0
    const adjustedHeight = height + extraHeight

    // Draw node background
    ctx.save()

    // Shadow - enhanced for search results
    if (isSearchResult) {
      ctx.shadowColor = 'rgba(255, 193, 7, 0.4)' // Yellow shadow for search results
      ctx.shadowBlur = 20
      ctx.shadowOffsetY = 6
    } else {
      ctx.shadowColor = 'rgba(0, 0, 0, 0.1)'
      ctx.shadowBlur = 10
      ctx.shadowOffsetY = 4
    }

    // Background based on level
    if (node.level === 'main') {
      const gradient = ctx.createLinearGradient(node.x - width/2, node.y - adjustedHeight/2, node.x + width/2, node.y + adjustedHeight/2)
      gradient.addColorStop(0, '#667eea')
      gradient.addColorStop(1, '#764ba2')
      ctx.fillStyle = gradient
    } else if (node.level === 'level-1') {
      const gradient = ctx.createLinearGradient(node.x - width/2, node.y - adjustedHeight/2, node.x + width/2, node.y + adjustedHeight/2)
      gradient.addColorStop(0, '#f093fb')
      gradient.addColorStop(1, '#f5576c')
      ctx.fillStyle = gradient
    } else {
      ctx.fillStyle = '#4facfe'
    }

    ctx.beginPath()
    ctx.roundRect(node.x - width/2, node.y - adjustedHeight/2, width, adjustedHeight, radius)
    ctx.fill()

    // Draw search highlight border
    if (isSearchResult) {
      ctx.strokeStyle = isSelectedResult ? '#f59e0b' : '#fbbf24'
      ctx.lineWidth = isSelectedResult ? 4 : 3
      ctx.beginPath()
      ctx.roundRect(node.x - width/2 - 2, node.y - adjustedHeight/2 - 2, width + 4, adjustedHeight + 4, radius + 2)
      ctx.stroke()

      // Add pulse effect for selected result
      if (isSelectedResult) {
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.3)'
        ctx.lineWidth = 8
        ctx.beginPath()
        ctx.roundRect(node.x - width/2 - 6, node.y - adjustedHeight/2 - 6, width + 12, adjustedHeight + 12, radius + 6)
        ctx.stroke()
      }
    }

    ctx.restore()

    // Draw text with proper wrapping
    ctx.fillStyle = 'white'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    // Title
    ctx.font = 'bold 14px Inter, sans-serif'
    const maxTitleWidth = width - 40
    const wrappedTitle = wrapText(ctx, cleanTitle, maxTitleWidth)
    const titleY = node.y - (extraHeight / 2) - 10

    if (wrappedTitle.length === 1) {
      ctx.fillText(wrappedTitle[0], node.x, titleY)
    } else {
      ctx.fillText(wrappedTitle[0], node.x, titleY - 8)
      ctx.fillText(wrappedTitle[1], node.x, titleY + 8)
    }

    // Draw source reference if available
    if (hasSourceRef) {
      ctx.font = '9px Inter, sans-serif'
      ctx.fillStyle = 'rgba(255, 255, 200, 0.9)'
      ctx.textAlign = 'center'
      const maxWidth = width - 20
      const wrappedSource = wrapText(ctx, `📖 ${sourceRef}`, maxWidth)
      const sourceY = node.y + (extraHeight / 2) - 5

      if (wrappedSource.length > 0) {
        ctx.fillText(wrappedSource[0].substring(0, 50) + (wrappedSource[0].length > 50 ? '...' : ''), node.x, sourceY)
      }
    }

    // Indicator per spiegazione dettagliata
    const hasExplanation = getNodeExplanation(node) !== null
    if (hasExplanation && !hasSourceRef) {
      ctx.font = '9px Inter, sans-serif'
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
      ctx.textAlign = 'center'
      ctx.fillText('ⓘ Shift+Click', node.x, node.y + 12)
    }

    // Draw expand indicator
    if (hasChildren(node.id) || onExpandNode) {
      const isExpanding = expandingNodes.has(node.id)
      ctx.beginPath()
      ctx.arc(node.x + width/2 - 10, node.y - adjustedHeight/2 + 10, 8, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
      ctx.fill()

      ctx.fillStyle = 'white'
      ctx.font = 'bold 12px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const indicator = isExpanding ? '…' : (node.expanded ? '−' : '+')
      ctx.fillText(indicator, node.x + width/2 - 10, node.y - adjustedHeight/2 + 10)
    }
  }

  const wrapText = (ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] => {
    // Input validation
    if (!text || typeof text !== 'string') {
      return ['']
    }

    const safeText = text.trim()
    if (!safeText) {
      return ['']
    }

    // Handle very long single words (URLs, IDs, etc.)
    const MAX_WORD_LENGTH = 20
    const words = safeText.split(' ').map(word => {
      if (word.length > MAX_WORD_LENGTH) {
        // Break long words
        const chunks = []
        for (let i = 0; i < word.length; i += MAX_WORD_LENGTH) {
          chunks.push(word.substring(i, i + MAX_WORD_LENGTH))
        }
        return chunks.join(' ')
      }
      return word
    }).join(' ').split(' ')

    const lines: string[] = []
    let currentLine = ''

    for (let i = 0; i < words.length; i++) {
      const word = words[i]

      if (!word) continue // Skip empty words

      let testLine = currentLine ? `${currentLine} ${word}` : word

      try {
        const width = ctx.measureText(testLine).width

        if (width < maxWidth || !currentLine) {
          currentLine = testLine
        } else {
          if (currentLine) {
            lines.push(currentLine)
            currentLine = word
          } else {
            // Single word too long, force it with truncation
            lines.push(word.substring(0, Math.max(5, maxWidth / 8)) + '...')
            currentLine = ''
          }
        }
      } catch (error) {
        console.warn('Error measuring text in wrapText:', error)
        // Fallback: simple character-based estimation
        if (testLine.length > maxWidth / 8) {
          if (currentLine) lines.push(currentLine)
          currentLine = word
        } else {
          currentLine = testLine
        }
      }
    }

    if (currentLine) {
      lines.push(currentLine)
    }

    // Return at most 2 lines with proper ellipsis
    if (lines.length === 0) {
      return ['']
    } else if (lines.length === 1) {
      return [lines[0]]
    } else if (lines.length === 2) {
      return lines
    } else {
      return [lines[0], lines[1] + '...']
    }
  }

  const drawConnection = (ctx: CanvasRenderingContext2D, from: MindmapNode, to: MindmapNode) => {
    ctx.beginPath()
    ctx.moveTo(from.x, from.y)

    // Curved connection
    const cx = (from.x + to.x) / 2
    const cy = (from.y + to.y) / 2 - 30

    ctx.quadraticCurveTo(cx, cy, to.x, to.y)

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)'
    ctx.lineWidth = 3
    ctx.lineCap = 'round'
    ctx.stroke()

    // Arrow
    const angle = Math.atan2(to.y - cy, to.x - cx)
    ctx.save()
    ctx.translate(to.x, to.y)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.moveTo(-10, -5)
    ctx.lineTo(0, 0)
    ctx.lineTo(-10, 5)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)'
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.restore()
  }

  const hasChildren = (nodeId: string): boolean => {
    if (!mindmapData) return false
    return mindmapData.connections.some(conn => conn.from === nodeId)
  }

  const collectChildIds = (connections: Connection[], parentId: string): string[] =>
    connections.filter(conn => conn.from === parentId).map(conn => conn.to)

  const getNodePath = (node: MindmapNode): StudyMindmapNode[] => {
    if (node.path.length) {
      return node.path
    }
    if (node.source) {
      return [node.source]
    }
    return []
  }

  const toggleNodeExpansion = (nodeId: string) => {
    console.log('🔍 Toggle node expansion called for:', nodeId)

    // First, handle the expansion logic before updating state
    const currentData = mindmapData
    if (!currentData) {
      console.warn('⚠️ No mindmap data available for expansion')
      return
    }

    const target = currentData.nodes.get(nodeId)
    if (!target) {
      console.warn('⚠️ Target node not found:', nodeId)
      return
    }

    const nextExpanded = !target.expanded
    console.log('📊 Node expansion state:', { nodeId, nextExpanded, currentlyExpanded: target.expanded })

    // If this is a collapse request or expansion without AI handler
    if (!nextExpanded || !onExpandNode) {
      // Regular toggle (collapse/expand without AI), just update the state
      setMindmapData(prev => {
        if (!prev) return prev
        const nodes = new Map(prev.nodes)
        const targetNode = nodes.get(nodeId)
        if (!targetNode) return prev

        nodes.set(nodeId, { ...targetNode, expanded: nextExpanded })

        const hideDescendants = (parentId: string) => {
          const childIds = collectChildIds(prev.connections, parentId)
          childIds.forEach(childId => {
            const child = nodes.get(childId)
            if (!child) return
            nodes.set(childId, { ...child, hidden: true })
            hideDescendants(childId)
          })
        }

        const showDescendants = (parentId: string) => {
          const childIds = collectChildIds(prev.connections, parentId)
          childIds.forEach(childId => {
            const child = nodes.get(childId)
            if (!child) return
            nodes.set(childId, { ...child, hidden: false })
            if (child.expanded) {
              showDescendants(childId)
            } else {
              hideDescendants(childId)
            }
          })
        }

        if (nextExpanded) {
          showDescendants(nodeId)
        } else {
          hideDescendants(nodeId)
        }

        return {
          ...prev,
          nodes
        }
      })
      return
    }

    // Check if we're using placeholder data and prevent AI expansion
    if (nextExpanded && onExpandNode && !expandingNodes.has(nodeId) && isPlaceholderData) {
      toast('⚠️ Genera una mappa concettuale reale prima di poter espandere i nodi con l\'AI', {
        icon: '🤖',
        style: {
          background: '#fef3c7',
          color: '#92400e',
          border: '1px solid #f59e0b',
        },
      })
      return
    }

    // If this is an expansion request with AI handler, show prompt dialog
    if (nextExpanded && onExpandNode && !expandingNodes.has(nodeId)) {
      const nodePath = getNodePath(target)
      console.log('🚀 Showing expand dialog for path:', nodePath.map(n => n.title))

      if (nodePath.length === 0) {
        console.warn('⚠️ Unable to determine node path for expansion', target)
        return
      }

      setExpandingNodeId(nodeId)
      setExpandPrompt('')
      setShowExpandDialog(true)
    }
  }

  const handleExpandWithPrompt = () => {
    if (!expandingNodeId || !mindmapData || !onExpandNode) {
      setShowExpandDialog(false)
      setExpandingNodeId(null)
      setExpandPrompt('')
      return
    }

    const target = mindmapData.nodes.get(expandingNodeId)
    if (!target) {
      console.warn('Target node not found for expansion:', expandingNodeId)
      setShowExpandDialog(false)
      setExpandingNodeId(null)
      setExpandPrompt('')
      return
    }

    const nodePath = getNodePath(target)
    if (nodePath.length === 0) {
      console.warn('Empty node path for expansion:', expandingNodeId)
      setShowExpandDialog(false)
      setExpandingNodeId(null)
      setExpandPrompt('')
      return
    }

    // Validate prompt
    const safePrompt = expandPrompt?.trim() || undefined
    if (safePrompt && safePrompt.length > 500) {
      toast('⚠️ Il prompt è troppo lungo, usa un messaggio più breve', {
        icon: '⚠️',
        style: { background: '#fef3c7', color: '#92400e' }
      })
      return
    }

    // Close dialog first
    setShowExpandDialog(false)

    // Set expanding state immediately
    setExpandingNodes(prevSet => {
      const copy = new Set(prevSet)
      copy.add(expandingNodeId)
      return copy
    })

    // Mark node as expanded immediately for better UX
    const nodes = new Map(mindmapData.nodes)
    nodes.set(expandingNodeId, { ...target, expanded: true })

    setMindmapData({
      ...mindmapData,
      nodes
    })

    // Clear dialog state
    setExpandingNodeId(null)
    setExpandPrompt('')

    // Call the expansion handler with custom prompt and proper error handling
    Promise.resolve(onExpandNode(nodePath, safePrompt))
      .then(() => {
        console.log('✅ Expansion completed successfully for:', expandingNodeId)
        toast.success('Nodo espanso con successo', { icon: '🎉' })
      })
      .catch((error) => {
        console.error('❌ Failed to expand mindmap node:', error)

        // Complete rollback on failure
        setMindmapData(prev => {
          if (!prev) return prev
          const revertNodes = new Map(prev.nodes)
          const revertTarget = revertNodes.get(expandingNodeId)
          if (revertTarget) {
            revertNodes.set(expandingNodeId, { ...revertTarget, expanded: false })
          }
          return {
            ...prev,
            nodes: revertNodes
          }
        })

        // Show user-friendly error message
        const errorMessage = error?.message || 'Errore durante l\'espansione del nodo'
        toast.error(errorMessage, { icon: '❌' })
      })
      .finally(() => {
        // Always remove from expanding set
        setExpandingNodes(prevSet => {
          const copy = new Set(prevSet)
          copy.delete(expandingNodeId)
          return copy
        })
      })
  }

  const handleCancelExpand = () => {
    setShowExpandDialog(false)
    setExpandingNodeId(null)
    setExpandPrompt('')
  }

  const handleSave = () => {
    if (mindmapData && onSave) {
      onSave(mindmapData)
    }
  }

  const handleExport = () => {
    if (mindmapData && onExport) {
      onExport(mindmapData)
    }
  }

  const handleReset = () => {
    createDefaultMindmap()
  }

  const handleForceRefresh = () => {
    autoLayoutAppliedRef.current = false
    if (data) {
      console.log('🔄 Force refresh triggered')
      createMindmapFromData(data)
    }
  }

  const handleZoomIn = () => {
    if (!mindmapData) return
    const newScale = Math.min(5, mindmapData.scale * 1.2)
    setMindmapData(prev => ({ ...prev, scale: newScale }))
  }

  const handleZoomOut = () => {
    if (!mindmapData) return
    const newScale = Math.max(0.1, mindmapData.scale / 1.2)
    setMindmapData(prev => ({ ...prev, scale: newScale }))
  }

  const handleZoomToFit = () => {
    if (!mindmapData || !canvasRef.current) return

    const nodes = Array.from(mindmapData.nodes.values()).filter(node => !node.hidden)
    if (nodes.length === 0) return

    // Find bounding box of all nodes
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    nodes.forEach(node => {
      const { width, height } = calculateNodeDimensions(node)
      minX = Math.min(minX, node.x - width/2)
      minY = Math.min(minY, node.y - height/2)
      maxX = Math.max(maxX, node.x + width/2)
      maxY = Math.max(maxY, node.y + height/2)
    })

    const contentWidth = maxX - minX + 100 // Add padding
    const contentHeight = maxY - minY + 100
    const canvasWidth = canvasRef.current.width
    const canvasHeight = canvasRef.current.height

    // Calculate scale to fit content in canvas
    const scaleX = (canvasWidth - 100) / contentWidth
    const scaleY = (canvasHeight - 200) / contentHeight
    const newScale = Math.min(1, Math.max(0.1, Math.min(scaleX, scaleY)))

    // Calculate center offset
    const contentCenterX = (minX + maxX) / 2
    const contentCenterY = (minY + maxY) / 2
    const newOffsetX = canvasWidth / 2 - contentCenterX * newScale
    const newOffsetY = canvasHeight / 2 - contentCenterY * newScale

    setMindmapData(prev => ({
      ...prev,
      scale: newScale,
      offset: { x: newOffsetX, y: newOffsetY }
    }))

    toast.success('Zoom adattato', { icon: '🎯' })
  }

  const handleZoomToSelection = () => {
    if (!mindmapData || !canvasRef.current) return

    // Use the currently highlighted search result if available
    const highlightedNodeId = searchResults[selectedSearchIndex]
    if (!highlightedNodeId) return

    const selectedNode = mindmapData.nodes.get(highlightedNodeId)
    if (!selectedNode) return

    const { width, height } = calculateNodeDimensions(selectedNode)
    const canvasWidth = canvasRef.current.width
    const canvasHeight = canvasRef.current.height

    // Center on selected node with some padding
    const newScale = Math.min(2, Math.max(0.5, 1))
    const newOffsetX = canvasWidth / 2 - selectedNode.x * newScale
    const newOffsetY = canvasHeight / 2 - selectedNode.y * newScale

    setMindmapData(prev => ({
      ...prev,
      scale: newScale,
      offset: { x: newOffsetX, y: newOffsetY }
    }))
  }

  const handleCenter = () => {
    if (!mindmapData) return
    const mainNode =
      mindmapData.nodes.get(ROOT_NODE_ID) ||
      Array.from(mindmapData.nodes.values()).find(node => node.level === 'main')

    if (mainNode && canvasRef.current) {
      const newOffsetX = canvasRef.current.width / 2 - mainNode.x * mindmapData.scale
      const newOffsetY = canvasRef.current.height / 2 - mainNode.y * mindmapData.scale

      setMindmapData(prev => ({
        ...prev,
        offset: { x: newOffsetX, y: newOffsetY }
      }))
    }
  }

  const handleSaveEdit = () => {
    if (!editingNode || !mindmapData) return

    // Validate input
    const safeTitle = editText.title?.trim() || 'Nodo'
    const safeSubtitle = editText.subtitle?.trim()

    if (safeTitle.length > 100) {
      toast('⚠️ Il titolo è troppo lungo (massimo 100 caratteri)', {
        icon: '⚠️',
        style: { background: '#fef3c7', color: '#92400e' }
      })
      return
    }

    if (safeSubtitle && safeSubtitle.length > 200) {
      toast('⚠️ La descrizione è troppo lunga (massimo 200 caratteri)', {
        icon: '⚠️',
        style: { background: '#fef3c7', color: '#92400e' }
      })
      return
    }

    const updatedNodes = new Map(mindmapData.nodes)
    const node = updatedNodes.get(editingNode)
    if (node) {
      updatedNodes.set(editingNode, {
        ...node,
        title: safeTitle,
        subtitle: safeSubtitle || undefined
      })
      setMindmapData(prev => prev ? { ...prev, nodes: updatedNodes } : prev)
      // Clear cache for this node since text changed
      dimensionsCache.current.clear()
    }

    setShowEditDialog(false)
    setEditingNode(null)
    setEditText({ title: '', subtitle: '' })
    toast.success('Nodo modificato con successo', { icon: '✅' })
  }

  const handleCancelEdit = () => {
    setShowEditDialog(false)
    setEditingNode(null)
    setEditText({ title: '', subtitle: '' })
  }

  // If no mindmap data, show empty state
  if (!mindmapData) {
    return (
      <div className={`relative w-full h-full bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center ${className}`}>
        <div className="text-center">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <RefreshCw className="h-10 w-10 text-blue-600 animate-spin" />
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">🧠 Mappa Concettuale Visuale</h3>
          <p className="text-gray-600">In attesa di dati per la mappa concettuale...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative w-full h-full bg-gradient-to-br from-purple-50 to-blue-50 ${className}`}>
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 bg-white/90 backdrop-blur-sm p-4 border-b border-gray-200 z-10">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">🧠 Mappa Concettuale Visuale</h2>
          <div className="flex gap-2">
            {/* Search Input */}
            <div className="relative">
              <input
                id="mindmap-search"
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  performSearch(e.target.value)
                }}
                placeholder="Cerca nodi..."
                className="pl-8 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
              />
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('')
                    setSearchResults([])
                    setSelectedSearchIndex(-1)
                  }}
                  className="absolute right-2 top-2.5 text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              )}
              {searchResults.length > 0 && (
                <div className="absolute top-full mt-1 right-0 bg-white border border-gray-200 rounded-lg shadow-lg p-2 text-xs z-20">
                  <div className="font-medium text-gray-700 mb-1">
                    {selectedSearchIndex + 1} di {searchResults.length} risultati
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => navigateToSearchResult(selectedSearchIndex - 1)}
                      disabled={selectedSearchIndex <= 0}
                      className="px-2 py-1 bg-gray-100 rounded disabled:opacity-50"
                      title="Precedente (Shift+F3)"
                    >
                      ↑
                    </button>
                    <button
                      onClick={() => navigateToSearchResult(selectedSearchIndex + 1)}
                      disabled={selectedSearchIndex >= searchResults.length - 1}
                      className="px-2 py-1 bg-gray-100 rounded disabled:opacity-50"
                      title="Successivo (F3)"
                    >
                      ↓
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Auto Layout Button */}
            <button
              onClick={performAutoLayout}
              disabled={isLayoutAnimating}
              className="px-3 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 flex items-center gap-1 text-sm"
              title="Riorganizza automaticamente i nodi"
            >
              {isLayoutAnimating ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Layout className="h-4 w-4" />
              )}
              Auto Layout
            </button>

            {/* Undo/Redo Buttons */}
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className="px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 flex items-center gap-1 text-sm"
              title="Annulla (Ctrl+Z)"
            >
              <Undo className="h-4 w-4" />
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className="px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 flex items-center gap-1 text-sm"
              title="Ripristina (Ctrl+Y)"
            >
              <Redo className="h-4 w-4" />
            </button>
            {editable && (
              <>
                <button
                  onClick={handleSave}
                  className="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-1 text-sm"
                >
                  <Save size={16} /> Salva
                </button>
                <button
                  onClick={handleExport}
                  className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-1 text-sm"
                >
                  <Download size={16} /> Esporta
                </button>
              </>
            )}
            <button
              onClick={handleForceRefresh}
              className="px-3 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center gap-1 text-sm"
            >
              <RefreshCw size={16} /> Refresh
            </button>
            <button
              onClick={handleReset}
              className="px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 flex items-center gap-1 text-sm"
            >
              <RefreshCw size={16} /> Reset
            </button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 border border-gray-200 z-10">
        <div className="flex flex-col gap-2">
          <button
            onClick={handleZoomIn}
            className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center"
            title="Zoom In (Ctrl +)"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleZoomOut}
            className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center"
            title="Zoom Out (Ctrl -)"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={handleZoomToFit}
            className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center"
            title="Adatta a tutto (Ctrl + 0)"
          >
            <span className="text-xs font-bold">⊡</span>
          </button>
          <button
            onClick={handleZoomToSelection}
            disabled={searchResults.length === 0 || selectedSearchIndex < 0}
            className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center disabled:opacity-50"
            title="Centra sulla selezione"
          >
            <span className="text-xs">⊙</span>
          </button>
          <button
            onClick={handleCenter}
            className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center"
            title="Centra radice"
          >
            <Move3D size={16} />
          </button>
        </div>
        {/* Zoom Level Display */}
        <div className="mt-2 pt-2 border-t border-gray-200">
          <div className="text-xs text-gray-600 text-center">
            {Math.round(mindmapData?.scale ? mindmapData.scale * 100 : 100)}%
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-20 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 border border-gray-200 z-10 max-w-xs">
        <h3 className="text-sm font-semibold text-gray-800 mb-2">📊 Statistiche</h3>
        <div className="text-xs text-gray-600 space-y-1">
          <div>Nodi: {stats.nodeCount}</div>
          <div>Collegamenti: {stats.connectionCount}</div>
          <div>Espansi: {stats.expandedCount}</div>
          <div>Zoom: {stats.zoomLevel}%</div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-800 mb-2">🔍 Debug Info</h4>
          <div className="text-xs text-gray-600 space-y-1">
            <div>Placeholder: {isPlaceholderData ? 'Sì' : 'No'}</div>
            <div>Data Sign: {dataSignature.substring(0, 15)}...</div>
            <div>Nodes in Map: {mindmapData?.nodes.size || 0}</div>
            <div>Connections: {mindmapData?.connections.length || 0}</div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-800 mb-2">🎯 Node Finder</h4>
          <input
            type="text"
            placeholder="Cerca nodo per ID..."
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
            onChange={(e) => {
              const searchId = e.target.value.trim()
              if (searchId && mindmapData) {
                const found = Array.from(mindmapData.nodes.values()).find(
                  node => node.source?.id === searchId || node.id === searchId
                )
                if (found) {
                  toast.success(`Nodo trovato: ${found.title?.substring(0, 30)}...`, { icon: '🎯' })
                } else {
                  toast.error(`Nodo ${searchId} non trovato`, { icon: '❌' })
                }
              }
            }}
          />
          <div className="mt-2 text-xs text-gray-500">
            Enter a node ID to test search functionality
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200">
          <button
            onClick={() => {
              if (mindmapData) {
                const allNodeIds = Array.from(mindmapData.nodes.values()).map(node => ({
                  visualId: node.id,
                  sourceId: node.source?.id || 'no-source',
                  title: node.title?.substring(0, 20) + '...'
                }))
                console.log('📋 All rendered nodes:', allNodeIds)
                console.log('🗂️ Mindmap data structure:', mindmapData)
                toast.success('Dati completati nella console', { icon: '📋' })
              }
            }}
            className="w-full px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Log All Nodes
          </button>
        </div>
      </div>

      {/* Canvas or empty CTA */}
      {mindmapData && mindmapData.nodes.size > 0 ? (
        <div ref={containerRef} className="absolute inset-0 mt-16">
          <canvas
            ref={canvasRef}
            className="w-full h-full"
          />
        </div>
      ) : (
        <div className="absolute inset-0 mt-16 flex items-center justify-center">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-6 border border-gray-200 text-center max-w-md">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Nessuna mappa disponibile</h3>
            <p className="text-sm text-gray-600 mb-4">Genera una mappa concettuale per iniziare a visualizzare i concetti principali.</p>
            <button
              onClick={onRegenerate ? onRegenerate : handleForceRefresh}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Rigenera Mindmap
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 border border-gray-200 z-10 max-w-xs">
        <h3 className="text-sm font-semibold text-gray-800 mb-2">🎮 Controlli</h3>
        <div className="text-xs text-gray-600 space-y-1">
          <div>• Trascina i nodi per muoverli</div>
          <div>• Click sui nodi per espandere</div>
          <div>• Shift+Click per vedere dettagli</div>
          <div>• Doppio click per modificare</div>
          <div>• Rotella mouse per zoom</div>
          <div>• Trascina sfondo per navigare</div>
        </div>
      </div>

      {/* Edit Dialog */}
      {showEditDialog && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Modifica Nodo</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Titolo
                </label>
                <input
                  type="text"
                  value={editText.title}
                  onChange={(e) => setEditText(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Inserisci titolo..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrizione (opzionale)
                </label>
                <textarea
                  value={editText.subtitle}
                  onChange={(e) => setEditText(prev => ({ ...prev, subtitle: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Inserisci descrizione..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                Annulla
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-md transition-colors"
              >
                Salva
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Expand Dialog */}
      {showExpandDialog && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Espandi Concetto</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Istruzioni per l'AI (opzionale)
                </label>
                <textarea
                  value={expandPrompt}
                  onChange={(e) => setExpandPrompt(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  rows={4}
                  placeholder="Esempi: &#10;• Approfondisci questo aspetto con esempi pratici&#10;• Aggiungi dettagli storici&#10;• Explora le implicazioni moderne&#10;• Confronta con altri concetti simili"
                />
              </div>

              <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-md">
                <p className="font-medium mb-1">💡 Suggerimenti:</p>
                <ul className="space-y-1">
                  <li>• Specifica cosa vuoi approfondire (es. "cause", "conseguenze", "esempi")</li>
                  <li>• Chiedi di collegare ad altri concetti correlati</li>
                  <li>• Richiedi prospettive diverse o contro-argomenti</li>
                </ul>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={handleCancelExpand}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                Annulla
              </button>
              <button
                onClick={handleExpandWithPrompt}
                className="px-4 py-2 bg-purple-600 text-white hover:bg-purple-700 rounded-md transition-colors flex items-center gap-2"
              >
                <Sparkles className="h-4 w-4" />
                Espandi con AI
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Explanation Dialog */}
      {showExplanationDialog && selectedExplanationNode && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-[600px] max-w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              📖 Dettagli Concetto
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Concetto
                </label>
                <div className="text-lg font-semibold text-blue-600">
                  {cleanNodeTitle(selectedExplanationNode.title)}
                </div>
              </div>

              {selectedExplanationNode.subtitle && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Spiegazione
                  </label>
                  <div className="text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-200">
                    {selectedExplanationNode.subtitle}
                  </div>
                </div>
              )}

              {selectedExplanationNode.source && (
                <>
                  {selectedExplanationNode.source.summary && selectedExplanationNode.source.summary !== selectedExplanationNode.subtitle && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Descrizione Estesa
                      </label>
                      <div className="text-gray-700 bg-blue-50 p-4 rounded-lg border border-blue-200">
                        {selectedExplanationNode.source.summary}
                      </div>
                    </div>
                  )}

                  {selectedExplanationNode.source.ai_hint && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        💡 Suggerimento AI
                      </label>
                      <div className="text-purple-700 bg-purple-50 p-4 rounded-lg border border-purple-200">
                        {selectedExplanationNode.source.ai_hint}
                      </div>
                    </div>
                  )}

                  {selectedExplanationNode.source.study_actions && selectedExplanationNode.source.study_actions.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        📚 Azioni di Studio Suggerite
                      </label>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 bg-green-50 p-4 rounded-lg border border-green-200">
                        {selectedExplanationNode.source.study_actions.map((action, index) => (
                          <li key={index}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedExplanationNode.path && selectedExplanationNode.path.length > 1 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        📍 Percorso Concettuale
                      </label>
                      <div className="text-gray-600 bg-amber-50 p-4 rounded-lg border border-amber-200">
                        {selectedExplanationNode.path.map(node => node.title).join(' → ')}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowExplanationDialog(false)
                  setSelectedExplanationNode(null)
                }}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
              >
                Chiudi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
