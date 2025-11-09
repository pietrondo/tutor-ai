/**
 * Interactive Tooltip for Concept Nodes
 * Shows detailed information and quick actions on hover
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen,
  Clock,
  Star,
  ChevronRight,
  Brain,
  Target,
  Bookmark,
  BookmarkCheck,
  Play,
  Eye,
  Zap
} from 'lucide-react'
import { ConceptNode } from '@/stores/conceptMapStore'

interface ConceptTooltipProps {
  node: ConceptNode
  position: { x: number; y: number }
  isVisible: boolean
  onMouseEnter: () => void
  onMouseLeave: () => void
  onQuickAction?: (action: string, nodeId: string) => void
  className?: string
}

export function ConceptTooltip({
  node,
  position,
  isVisible,
  onMouseEnter,
  onMouseLeave,
  onQuickAction,
  className = ''
}: ConceptTooltipProps) {
  const [isBookmarked, setIsBookmarked] = useState(false)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const [adjustedPosition, setAdjustedPosition] = useState(position)

  // Adjust tooltip position to stay within viewport
  useEffect(() => {
    if (isVisible && tooltipRef.current) {
      const tooltip = tooltipRef.current
      const rect = tooltip.getBoundingClientRect()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight

      let adjustedX = position.x
      let adjustedY = position.y

      // Adjust horizontal position
      if (position.x + rect.width > viewportWidth - 20) {
        adjustedX = viewportWidth - rect.width - 20
      }
      if (adjustedX < 20) {
        adjustedX = 20
      }

      // Adjust vertical position
      if (position.y + rect.height > viewportHeight - 20) {
        adjustedY = position.y - rect.height - 10
      }
      if (adjustedY < 20) {
        adjustedY = 20
      }

      setAdjustedPosition({ x: adjustedX, y: adjustedY })
    }
  }, [position, isVisible])

  const handleQuickAction = (action: string) => {
    if (onQuickAction) {
      onQuickAction(action, node.id)
    }
  }

  const masteryColor = node.masteryLevel
    ? node.masteryLevel >= 80 ? 'text-green-600'
    : node.masteryLevel >= 50 ? 'text-yellow-600'
    : 'text-red-600'
    : 'text-gray-400'

  const priorityColor = node.priority
    ? node.priority >= 4 ? 'bg-red-100 text-red-700 border-red-200'
    : node.priority >= 3 ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
    : 'bg-blue-100 text-blue-700 border-blue-200'
    : 'bg-gray-100 text-gray-700 border-gray-200'

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          ref={tooltipRef}
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={`fixed z-[9999] bg-white rounded-lg shadow-2xl border border-gray-200 p-4 min-w-80 max-w-96 ${className}`}
          style={{
            left: `${adjustedPosition.x}px`,
            top: `${adjustedPosition.y}px`,
            maxHeight: '70vh',
            overflowY: 'auto'
          }}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 text-sm leading-tight mb-1">
                {node.title}
              </h3>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                {node.depth !== undefined && (
                  <span className="flex items-center gap-1">
                    <ChevronRight className="h-3 w-3" />
                    Livello {node.depth}
                  </span>
                )}
                {node.visited && (
                  <span className="flex items-center gap-1">
                    <Eye className="h-3 w-3" />
                    Visitato
                  </span>
                )}
                {node.lastVisited && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(node.lastVisited).toLocaleDateString('it-IT')}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={() => handleQuickAction('toggle-bookmark')}
              className="ml-2 p-1 rounded-md hover:bg-gray-100 transition-colors"
            >
              {isBookmarked ? (
                <BookmarkCheck className="h-4 w-4 text-blue-600" />
              ) : (
                <Bookmark className="h-4 w-4 text-gray-400 hover:text-blue-600" />
              )}
            </button>
          </div>

          {/* Summary */}
          {node.summary && (
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {node.summary}
            </p>
          )}

          {/* Metadata */}
          <div className="space-y-2 mb-3">
            {/* Priority Badge */}
            {node.priority && (
              <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${priorityColor}`}>
                <Target className="h-3 w-3" />
                Priorità {node.priority}/5
              </div>
            )}

            {/* Mastery Level */}
            {node.masteryLevel !== undefined && (
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium ${masteryColor}`}>
                  Mastery: {node.masteryLevel}%
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      node.masteryLevel >= 80 ? 'bg-green-500' :
                      node.masteryLevel >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${node.masteryLevel}%` }}
                  />
                </div>
              </div>
            )}

            {/* Children Count */}
            {node.children && node.children.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <BookOpen className="h-3 w-3" />
                {node.children.length} sotto-concett{node.children.length === 1 ? 'o' : 'i'}
              </div>
            )}

            {/* Tags */}
            {node.tags && node.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {node.tags.slice(0, 3).map(tag => (
                  <span
                    key={tag}
                    className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md"
                  >
                    {tag}
                  </span>
                ))}
                {node.tags.length > 3 && (
                  <span className="text-xs text-gray-400">
                    +{node.tags.length - 3}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* AI Hint */}
          {node.ai_hint && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-2 mb-3">
              <div className="flex items-start gap-2">
                <Brain className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-blue-700 italic">
                  {node.ai_hint}
                </p>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="border-t border-gray-100 pt-3">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleQuickAction('expand')}
                className="flex items-center justify-center gap-1 px-3 py-2 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors"
              >
                <Zap className="h-3 w-3" />
                Espandi
              </button>
              <button
                onClick={() => handleQuickAction('study')}
                className="flex items-center justify-center gap-1 px-3 py-2 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 transition-colors"
              >
                <Play className="h-3 w-3" />
                Studia
              </button>
              <button
                onClick={() => handleQuickAction('quiz')}
                className="flex items-center justify-center gap-1 px-3 py-2 bg-purple-600 text-white text-xs rounded-md hover:bg-purple-700 transition-colors"
              >
                <Target className="h-3 w-3" />
                Quiz
              </button>
              <button
                onClick={() => handleQuickAction('details')}
                className="flex items-center justify-center gap-1 px-3 py-2 bg-gray-600 text-white text-xs rounded-md hover:bg-gray-700 transition-colors"
              >
                <Eye className="h-3 w-3" />
                Dettagli
              </button>
            </div>
          </div>

          {/* Study Actions */}
          {node.study_actions && node.study_actions.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <p className="text-xs font-medium text-gray-700 mb-2">Azioni suggerite:</p>
              <ul className="space-y-1">
                {node.study_actions.slice(0, 2).map((action, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start gap-1">
                    <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                    <span className="line-clamp-1">{action}</span>
                  </li>
                ))}
                {node.study_actions.length > 2 && (
                  <li className="text-xs text-blue-600 hover:text-blue-700 cursor-pointer">
                    +{node.study_actions.length - 2} altre azioni
                  </li>
                )}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Higher-order component for tooltip integration
export function withTooltip<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function TooltipComponent(props: P & {
    node: ConceptNode
    onQuickAction?: (action: string, nodeId: string) => void
  }) {
    const [tooltipVisible, setTooltipVisible] = useState(false)
    const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
    const elementRef = useRef<HTMLDivElement>(null)

    const handleMouseEnter = (e: React.MouseEvent) => {
      if (elementRef.current) {
        const rect = elementRef.current.getBoundingClientRect()
        const viewportWidth = window.innerWidth
        const viewportHeight = window.innerHeight

        // Calculate tooltip position with boundary checks
        let tooltipX = rect.right + 10
        let tooltipY = rect.top

        // Check if tooltip would go out of viewport on the right
        if (rect.right + 320 > viewportWidth) { // 320px is approximate tooltip width
          tooltipX = rect.left - 320 // Position on the left instead
        }

        // Check if tooltip would go out of viewport at the bottom
        if (rect.top + 200 > viewportHeight) { // 200px is approximate tooltip height
          tooltipY = viewportHeight - 210 // Position higher up
        }

        setTooltipPosition({ x: tooltipX, y: tooltipY })
        setTooltipVisible(true)
      }
    }

    const handleMouseLeave = () => {
      setTooltipVisible(false)
    }

    return (
      <>
        <div
          ref={elementRef}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className="inline-block relative z-10"
        >
          <WrappedComponent {...props} />
        </div>

        {/* Render tooltip in a portal to avoid overflow issues */}
        {tooltipVisible && createPortal(
          <ConceptTooltip
            node={props.node}
            position={tooltipPosition}
            isVisible={tooltipVisible}
            onMouseEnter={() => setTooltipVisible(true)}
            onMouseLeave={() => setTooltipVisible(false)}
            onQuickAction={props.onQuickAction}
          />,
          document.body
        )}
      </>
    )
  }
}