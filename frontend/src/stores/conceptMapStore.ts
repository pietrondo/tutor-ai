/**
 * Concept Map State Management
 * Shared state for all concept map visualizations and interactions
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

// Types for concept map state
export interface ConceptNode {
  id: string
  title: string
  summary?: string
  description?: string
  ai_hint?: string
  study_actions: string[]
  priority?: number | null
  references?: string[]
  children: ConceptNode[]
  expanded?: boolean
  visited?: boolean
  bookmarked?: boolean
  masteryLevel?: number
  lastVisited?: string
  tags?: string[]
  sourceType?: 'course' | 'book' | 'ai_generated'
  parentId?: string
  depth?: number
  position?: { x: number; y: number }
}

export interface ConceptMapState {
  // Core data
  rootNode: ConceptNode | null
  nodes: Map<string, ConceptNode>
  selectedNodeId: string | null
  hoveredNodeId: string | null

  // Navigation state
  breadcrumb: ConceptNode[]
  navigationHistory: string[]
  historyIndex: number

  // View state
  viewMode: 'visual' | 'explorer' | 'both'
  zoom: number
  panOffset: { x: number; y: number }

  // UI state
  isLoading: boolean
  expandedNodes: Set<string>
  bookmarkedNodes: Set<string>
  searchQuery: string
  searchResults: string[]

  // Interaction state
  isDragging: boolean
  draggedNodeId: string | null
  contextMenuNodeId: string | null
  contextMenuPosition: { x: number; y: number } | null

  // Learning integration
  currentCourseId: string | null
  currentBookId: string | null
  showProgressIndicators: boolean
  showAIHints: boolean

  // Actions
  setRootNode: (node: ConceptNode) => void
  selectNode: (nodeId: string | null) => void
  hoverNode: (nodeId: string | null) => void
  toggleNodeExpansion: (nodeId: string) => void
  expandNode: (nodeId: string) => void
  collapseNode: (nodeId: string) => void
  expandAll: () => void
  collapseAll: () => void

  // Navigation actions
  navigateToNode: (nodeId: string) => void
  navigateBack: () => void
  navigateForward: () => void
  updateBreadcrumb: (node: ConceptNode) => void

  // Bookmark actions
  toggleBookmark: (nodeId: string) => void
  isBookmarked: (nodeId: string) => boolean

  // Search actions
  setSearchQuery: (query: string) => void
  searchNodes: (query: string) => void
  clearSearch: () => void

  // View actions
  setViewMode: (mode: 'visual' | 'explorer' | 'both') => void
  setZoom: (zoom: number) => void
  setPanOffset: (offset: { x: number; y: number }) => void
  centerView: () => void

  // Context menu actions
  showContextMenu: (nodeId: string, position: { x: number; y: number }) => void
  hideContextMenu: () => void

  // Learning integration
  setCurrentContext: (courseId: string | null, bookId: string | null) => void
  markNodeAsVisited: (nodeId: string) => void
  updateMasteryLevel: (nodeId: string, level: number) => void

  // Node management
  addNode: (node: ConceptNode, parentId?: string) => void
  updateNode: (nodeId: string, updates: Partial<ConceptNode>) => void
  removeNode: (nodeId: string) => void

  // AI expansion
  expandNodeWithAI: (nodeId: string, prompt?: string) => Promise<void>

  // Utility actions
  reset: () => void
  getNodePath: (nodeId: string) => ConceptNode[]
  findNode: (nodeId: string) => ConceptNode | null
}

export const useConceptMapStore = create<ConceptMapState>()(
  devtools(
    (set, get) => ({
      // Initial state
      rootNode: null,
      nodes: new Map(),
      selectedNodeId: null,
      hoveredNodeId: null,

      breadcrumb: [],
      navigationHistory: [],
      historyIndex: -1,

      viewMode: 'visual',
      zoom: 1,
      panOffset: { x: 0, y: 0 },

      isLoading: false,
      expandedNodes: new Set(),
      bookmarkedNodes: new Set(),
      searchQuery: '',
      searchResults: [],

      isDragging: false,
      draggedNodeId: null,
      contextMenuNodeId: null,
      contextMenuPosition: null,

      currentCourseId: null,
      currentBookId: null,
      showProgressIndicators: true,
      showAIHints: true,

      // Actions implementation
      setRootNode: (node) => {
        // Validate node before processing
        if (!node || !node.id) {
          console.error('Invalid root node provided to setRootNode:', node)
          return // Don't update state if node is invalid
        }

        set((state) => {
          const nodes = new Map<string, ConceptNode>()
          const buildNodesMap = (n: ConceptNode) => {
            if (!n || !n.id) {
              console.error('Invalid node in buildNodesMap:', n)
              return
            }
            nodes.set(n.id, n)
            if (n.children && Array.isArray(n.children)) {
              n.children.forEach(buildNodesMap)
            }
          }
          buildNodesMap(node)

          return {
            rootNode: node,
            nodes,
            selectedNodeId: node.id,
            breadcrumb: [node],
            navigationHistory: [node.id],
            historyIndex: 0,
            expandedNodes: new Set([node.id])
          }
        })
      },

      selectNode: (nodeId) => {
        set({ selectedNodeId: nodeId })
        const node = get().nodes.get(nodeId)
        if (node) {
          get().markNodeAsVisited(nodeId)
          get().updateBreadcrumb(node)
        }
      },

      hoverNode: (nodeId) => set({ hoveredNodeId: nodeId }),

      toggleNodeExpansion: (nodeId) => {
        set((state) => {
          const expanded = new Set(state.expandedNodes)
          if (expanded.has(nodeId)) {
            expanded.delete(nodeId)
          } else {
            expanded.add(nodeId)
          }
          return { expandedNodes: expanded }
        })
      },

      expandNode: (nodeId) => {
        set((state) => ({
          expandedNodes: new Set([...state.expandedNodes, nodeId])
        }))
      },

      collapseNode: (nodeId) => {
        set((state) => {
          const expanded = new Set(state.expandedNodes)
          expanded.delete(nodeId)
          return { expandedNodes: expanded }
        })
      },

      expandAll: () => {
        set((state) => ({
          expandedNodes: new Set(state.nodes.keys())
        }))
      },

      collapseAll: () => {
        set({ expandedNodes: new Set() })
      },

      navigateToNode: (nodeId) => {
        const state = get()
        const node = state.nodes.get(nodeId)
        if (!node) return

        // Update navigation history
        const newHistory = state.navigationHistory.slice(0, state.historyIndex + 1)
        newHistory.push(nodeId)

        set((prev) => ({
          selectedNodeId: nodeId,
          navigationHistory: newHistory,
          historyIndex: newHistory.length - 1
        }))

        get().selectNode(nodeId)
        get().expandNode(nodeId)
      },

      navigateBack: () => {
        const state = get()
        if (state.historyIndex > 0) {
          const newIndex = state.historyIndex - 1
          const nodeId = state.navigationHistory[newIndex]
          set({
            historyIndex: newIndex,
            selectedNodeId: nodeId
          })
          get().selectNode(nodeId)
        }
      },

      navigateForward: () => {
        const state = get()
        if (state.historyIndex < state.navigationHistory.length - 1) {
          const newIndex = state.historyIndex + 1
          const nodeId = state.navigationHistory[newIndex]
          set({
            historyIndex: newIndex,
            selectedNodeId: nodeId
          })
          get().selectNode(nodeId)
        }
      },

      updateBreadcrumb: (node) => {
        const path = get().getNodePath(node.id)
        set({ breadcrumb: path })
      },

      toggleBookmark: (nodeId) => {
        set((state) => {
          const bookmarked = new Set(state.bookmarkedNodes)
          if (bookmarked.has(nodeId)) {
            bookmarked.delete(nodeId)
          } else {
            bookmarked.add(nodeId)
          }
          return { bookmarkedNodes: bookmarked }
        })
      },

      isBookmarked: (nodeId) => {
        return get().bookmarkedNodes.has(nodeId)
      },

      setSearchQuery: (query) => set({ searchQuery: query }),

      searchNodes: (query) => {
        if (!query.trim()) {
          set({ searchResults: [] })
          return
        }

        const state = get()
        const results: string[] = []
        const lowerQuery = query.toLowerCase()

        state.nodes.forEach((node) => {
          if (
            node.title.toLowerCase().includes(lowerQuery) ||
            node.summary?.toLowerCase().includes(lowerQuery) ||
            node.description?.toLowerCase().includes(lowerQuery) ||
            node.tags?.some(tag => tag.toLowerCase().includes(lowerQuery))
          ) {
            results.push(node.id)
          }
        })

        set({ searchResults: results })
      },

      clearSearch: () => set({ searchQuery: '', searchResults: [] }),

      setViewMode: (mode) => set({ viewMode: mode }),

      setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),

      setPanOffset: (offset) => set({ panOffset: offset }),

      centerView: () => {
        set({ zoom: 1, panOffset: { x: 0, y: 0 } })
      },

      showContextMenu: (nodeId, position) => {
        set({
          contextMenuNodeId: nodeId,
          contextMenuPosition: position
        })
      },

      hideContextMenu: () => {
        set({
          contextMenuNodeId: null,
          contextMenuPosition: null
        })
      },

      setCurrentContext: (courseId, bookId) => {
        set({ currentCourseId: courseId, currentBookId: bookId })
      },

      markNodeAsVisited: (nodeId) => {
        set((state) => {
          const nodes = new Map(state.nodes)
          const node = nodes.get(nodeId)
          if (node) {
            node.visited = true
            node.lastVisited = new Date().toISOString()
            nodes.set(nodeId, node)
          }
          return { nodes }
        })
      },

      updateMasteryLevel: (nodeId, level) => {
        set((state) => {
          const nodes = new Map(state.nodes)
          const node = nodes.get(nodeId)
          if (node) {
            node.masteryLevel = level
            nodes.set(nodeId, node)
          }
          return { nodes }
        })
      },

      addNode: (node, parentId) => {
        set((state) => {
          const nodes = new Map(state.nodes)
          nodes.set(node.id, { ...node, depth: parentId ? (nodes.get(parentId)?.depth || 0) + 1 : 0 })

          if (parentId) {
            const parent = nodes.get(parentId)
            if (parent) {
              parent.children = [...parent.children, node]
              nodes.set(parentId, parent)
            }
          }

          return { nodes }
        })
      },

      updateNode: (nodeId, updates) => {
        set((state) => {
          const nodes = new Map(state.nodes)
          const node = nodes.get(nodeId)
          if (node) {
            const updatedNode = { ...node, ...updates }
            nodes.set(nodeId, updatedNode)

            // Update in parent's children if needed
            if (node.parentId) {
              const parent = nodes.get(node.parentId)
              if (parent) {
                parent.children = parent.children.map(child =>
                  child.id === nodeId ? updatedNode : child
                )
                nodes.set(node.parentId, parent)
              }
            }

            // Update root node if needed
            if (state.rootNode?.id === nodeId) {
              return { nodes, rootNode: updatedNode }
            }
          }
          return { nodes }
        })
      },

      removeNode: (nodeId) => {
        set((state) => {
          const nodes = new Map(state.nodes)
          const node = nodes.get(nodeId)

          if (node) {
            // Remove from parent's children
            if (node.parentId) {
              const parent = nodes.get(node.parentId)
              if (parent) {
                parent.children = parent.children.filter(child => child.id !== nodeId)
                nodes.set(node.parentId, parent)
              }
            }

            // Remove node and all its descendants
            const removeRecursive = (n: ConceptNode) => {
              nodes.delete(n.id)
              n.children.forEach(removeRecursive)
            }
            removeRecursive(node)
          }

          return { nodes }
        })
      },

      expandNodeWithAI: async (nodeId, prompt) => {
        const state = get()
        if (!state.currentCourseId) return

        set({ isLoading: true })

        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/mindmap/expand`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              course_id: state.currentCourseId,
              book_id: state.currentBookId,
              node_id: nodeId,
              prompt: prompt || `Espandi questo concetto con sottotemi correlati e dettagli importanti`
            })
          })

          if (response.ok) {
            const data = await response.json()
            if (data.expanded_nodes && data.expanded_nodes.length > 0) {
              data.expanded_nodes.forEach((newNode: ConceptNode) => {
                get().addNode(newNode, nodeId)
              })
              get().expandNode(nodeId)
            }
          }
        } catch (error) {
          console.error('Error expanding node with AI:', error)
        } finally {
          set({ isLoading: false })
        }
      },

      reset: () => {
        set({
          rootNode: null,
          nodes: new Map(),
          selectedNodeId: null,
          hoveredNodeId: null,
          breadcrumb: [],
          navigationHistory: [],
          historyIndex: -1,
          expandedNodes: new Set(),
          bookmarkedNodes: new Set(),
          searchQuery: '',
          searchResults: [],
          zoom: 1,
          panOffset: { x: 0, y: 0 }
        })
      },

      getNodePath: (nodeId) => {
        const state = get()
        const path: ConceptNode[] = []
        let currentId: string | undefined = nodeId

        while (currentId) {
          const node = state.nodes.get(currentId)
          if (!node) break

          path.unshift(node)
          currentId = node.parentId
        }

        return path
      },

      findNode: (nodeId) => {
        return get().nodes.get(nodeId) || null
      }
    }),
    {
      name: 'concept-map-store'
    }
  )
)