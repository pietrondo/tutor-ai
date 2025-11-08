/**
 * Animated Concept Node with smooth expand/collapse transitions
 * Provides fluid animations for concept map interactions
 */

'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence, useAnimation } from 'framer-motion'
import {
  ChevronRight,
  ChevronDown,
  Plus,
  Brain,
  Loader2,
  Sparkles,
  Eye,
  EyeOff
} from 'lucide-react'
import { ConceptNode } from '@/stores/conceptMapStore'
import { useConceptMapStore } from '@/stores/conceptMapStore'
import { ConceptTooltip } from './ConceptTooltip'

interface AnimatedConceptNodeProps {
  node: ConceptNode
  isExpanded?: boolean
  isRoot?: boolean
  depth?: number
  onNodeClick?: (node: ConceptNode) => void
  onExpandRequest?: (nodeId: string, useAI?: boolean) => void
  className?: string
  children?: React.ReactNode
}

const nodeVariants = {
  hidden: {
    opacity: 0,
    scale: 0.8,
    y: -10
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20,
      mass: 0.5
    }
  },
  expanded: {
    scale: 1.02,
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  collapsed: {
    scale: 1,
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  }
}

const childrenVariants = {
  hidden: {
    opacity: 0,
    height: 0,
    x: -20
  },
  visible: {
    opacity: 1,
    height: "auto",
    x: 0,
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 15,
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  }
}

const childItemVariants = {
  hidden: {
    opacity: 0,
    x: -20,
    scale: 0.9
  },
  visible: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20
    }
  }
}

export function AnimatedConceptNode({
  node,
  isExpanded = false,
  isRoot = false,
  depth = 0,
  onNodeClick,
  onExpandRequest,
  className = '',
  children
}: AnimatedConceptNodeProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isAIExpanding, setIsAIExpanding] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })

  const controls = useAnimation()
  const nodeRef = useRef<HTMLDivElement>(null)
  const childrenContainerRef = useRef<HTMLDivElement>(null)

  const {
    expandedNodes,
    selectedNodeId,
    selectNode,
    toggleNodeExpansion,
    expandNodeWithAI,
    isLoading
  } = useConceptMapStore()

  const isExpandedInStore = expandedNodes.has(node.id)
  const isSelected = selectedNodeId === node.id
  const hasChildren = node.children && node.children.length > 0

  // Update animation state when expansion changes
  useEffect(() => {
    if (isExpandedInStore) {
      controls.start('expanded')
    } else {
      controls.start('collapsed')
    }
  }, [isExpandedInStore, controls])

  const handleNodeClick = () => {
    selectNode(node.id)
    onNodeClick?.(node)
  }

  const handleExpandToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    toggleNodeExpansion(node.id)
  }

  const handleAIExpand = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!isAIExpanding) {
      setIsAIExpanding(true)
      try {
        await expandNodeWithAI(node.id, `Espandi il concetto "${node.title}" con sottotemi correlati e dettagli importanti`)
        onExpandRequest?.(node.id, true)
      } finally {
        setIsAIExpanding(false)
      }
    }
  }

  const handleQuickAction = (action: string, nodeId: string) => {
    switch (action) {
      case 'expand':
        toggleNodeExpansion(nodeId)
        break
      case 'ai-expand':
        handleAIExpand({} as React.MouseEvent)
        break
      case 'toggle-bookmark':
        // Handle bookmark toggle
        break
      case 'study':
        // Handle study action
        break
      case 'quiz':
        // Handle quiz action
        break
      case 'details':
        // Handle details view
        break
    }
  }

  const handleMouseEnter = (e: React.MouseEvent) => {
    setIsHovered(true)
    if (nodeRef.current) {
      const rect = nodeRef.current.getBoundingClientRect()
      setTooltipPosition({
        x: rect.right + 10,
        y: rect.top
      })
      setShowTooltip(true)
    }
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
    setShowTooltip(false)
  }

  // Enhanced depth and concept type-based styling
  const getDepthStyles = (depth: number, conceptType?: string) => {
    const isMacro = conceptType === 'macro'
    const isSub = conceptType === 'sub'

    if (depth === 0) {
      return 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-xl border-2 border-blue-800'
    }

    if (depth === 1 && isMacro) {
      return 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg border-2 border-purple-700'
    }

    if (depth === 2 && isSub) {
      return 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-md border-2 border-indigo-700'
    }

    if (depth >= 2) {
      return 'bg-white border-2 border-gray-300 text-gray-800 shadow-sm hover:border-gray-400'
    }

    return 'bg-white border-2 border-gray-200 text-gray-700 shadow-sm hover:border-gray-300'
  }

  const nodeStyle = getDepthStyles(depth, node.metadata?.conceptType)

  const masteryIndicator = node.masteryLevel !== undefined ? (
    <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 ${
      node.masteryLevel >= 80 ? 'bg-green-500 border-white' :
      node.masteryLevel >= 50 ? 'bg-yellow-500 border-white' : 'bg-red-500 border-white'
    }`} />
  ) : null

  const visitedIndicator = node.visited ? (
    <div className="absolute top-1 left-1 w-2 h-2 bg-white/50 rounded-full" />
  ) : null

  return (
    <div className={`relative ${className}`}>
      {/* Main Node */}
      <motion.div
        ref={nodeRef}
        variants={nodeVariants}
        initial="hidden"
        animate="visible"
        whileHover="expanded"
        className={`
          relative px-4 py-3 rounded-lg cursor-pointer transition-all duration-200
          ${nodeStyle}
          ${isSelected ? 'ring-2 ring-blue-400 ring-offset-2' : ''}
          ${isHovered ? 'shadow-xl transform -translate-y-0.5' : ''}
        `}
        onClick={handleNodeClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        layout
      >
        {/* Indicators */}
        {masteryIndicator}
        {visitedIndicator}

        {/* Node Content */}
        <div className="flex items-center gap-3">
          {/* Expand/Collapse Icon */}
          {hasChildren && (
            <motion.button
              onClick={handleExpandToggle}
              className="p-1 rounded-md hover:bg-white/20 transition-colors"
              animate={{ rotate: isExpandedInStore ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight className="h-4 w-4" />
            </motion.button>
          )}

          {/* Node Title */}
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-sm leading-tight mb-1">
              {node.title}
            </h3>
            {node.summary && (
              <p className="text-xs opacity-80 line-clamp-2">
                {node.summary}
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1">
            {/* AI Expand Button */}
            {depth < 3 && (
              <motion.button
                onClick={handleAIExpand}
                disabled={isAIExpanding || isLoading}
                className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 transition-all duration-200 disabled:opacity-50"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                {isAIExpanding ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Brain className="h-3.5 w-3.5" />
                )}
              </motion.button>
            )}

            {/* Add Child Button */}
            {isExpandedInStore && (
              <motion.button
                onClick={(e) => {
                  e.stopPropagation()
                  onExpandRequest?.(node.id, false)
                }}
                className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 transition-all duration-200"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Plus className="h-3.5 w-3.5" />
              </motion.button>
            )}
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-3 mt-2 text-xs opacity-70">
          {/* Concept Type Badge */}
          <div className="flex items-center gap-1">
            {node.metadata?.conceptType === 'macro' && (
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">
                📖 Macro
              </span>
            )}
            {node.metadata?.conceptType === 'sub' && (
              <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full font-medium">
                🔍 Dettaglio
              </span>
            )}
            {node.metadata?.canExpand && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-medium">
                ✨ Espandibile
              </span>
            )}
          </div>

          {/* Chapter Info */}
          {node.metadata?.chapterInfo && node.metadata.chapterInfo.type === 'chapter' && (
            <span className="flex items-center gap-1">
              📚 Cap. {node.metadata.chapterInfo.index}
            </span>
          )}

          {/* Sub-concepts count */}
          {node.metadata?.subConceptsCount && node.metadata.subConceptsCount > 0 && (
            <span>{node.metadata.subConceptsCount} sotto-concett{i => i.length === 1 ? 'o' : 'i'}</span>
          )}

          {/* Level indicator */}
          {node.depth !== undefined && depth > 0 && (
            <span>Livello {node.depth}</span>
          )}

          {/* Tags */}
          {node.tags && node.tags.length > 0 && (
            <div className="flex gap-1">
              {node.tags.slice(0, 2).map(tag => (
                <span key={tag} className="px-2 py-0.5 bg-black/10 rounded-full text-xs">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* AI Hint */}
        {node.ai_hint && isExpandedInStore && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 p-2 bg-black/10 rounded-md text-xs"
          >
            <div className="flex items-start gap-2">
              <Sparkles className="h-3 w-3 mt-0.5 flex-shrink-0" />
              <p className="italic">{node.ai_hint}</p>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Children Container */}
      <AnimatePresence>
        {isExpandedInStore && hasChildren && (
          <motion.div
            ref={childrenContainerRef}
            variants={childrenVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="ml-6 mt-3 space-y-2"
          >
            {node.children.map((child, index) => (
              <motion.div
                key={child.id}
                variants={childItemVariants}
                custom={index}
                layout
              >
                <AnimatedConceptNode
                  node={child}
                  depth={depth + 1}
                  onNodeClick={onNodeClick}
                  onExpandRequest={onExpandRequest}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tooltip */}
      <ConceptTooltip
        node={node}
        position={tooltipPosition}
        isVisible={showTooltip}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onQuickAction={handleQuickAction}
      />
    </div>
  )
}

// Hook for managing expand/collapse animations
export function useExpandAnimation() {
  const [animatingNodes, setAnimatingNodes] = useState<Set<string>>(new Set())

  const animateExpansion = async (nodeId: string, isExpanding: boolean) => {
    setAnimatingNodes(prev => new Set([...prev, nodeId]))

    // Wait for animation to complete
    await new Promise(resolve => setTimeout(resolve, 300))

    setAnimatingNodes(prev => {
      const newSet = new Set(prev)
      newSet.delete(nodeId)
      return newSet
    })
  }

  return {
    animatingNodes,
    animateExpansion,
    isAnimating: (nodeId: string) => animatingNodes.has(nodeId)
  }
}

// Loading skeleton for concept nodes
export function ConceptNodeSkeleton({ depth = 0 }: { depth?: number }) {
  return (
    <div className={`relative ${depth > 0 ? 'ml-6' : ''}`}>
      <div className="px-4 py-3 rounded-lg bg-gray-100 border border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 bg-gray-300 rounded animate-pulse" />
          <div className="flex-1">
            <div className="h-4 bg-gray-300 rounded w-3/4 mb-2 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  )
}