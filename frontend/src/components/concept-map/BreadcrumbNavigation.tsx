/**
 * Breadcrumb Navigation for Concept Maps
 * Shows the hierarchical path to the current concept
 */

'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronRight,
  Home,
  BookOpen,
  ArrowLeft,
  ArrowRight,
  MoreHorizontal
} from 'lucide-react'
import { ConceptNode } from '@/stores/conceptMapStore'
import { useConceptMapStore } from '@/stores/conceptMapStore'

interface BreadcrumbNavigationProps {
  className?: string
  showNavigationButtons?: boolean
  maxItems?: number
}

export function BreadcrumbNavigation({
  className = '',
  showNavigationButtons = true,
  maxItems = 5
}: BreadcrumbNavigationProps) {
  const {
    breadcrumb,
    selectedNodeId,
    navigateBack,
    navigateForward,
    navigationHistory,
    historyIndex,
    rootNode
  } = useConceptMapStore()

  const canNavigateBack = historyIndex > 0
  const canNavigateForward = historyIndex < navigationHistory.length - 1

  // Handle case where we have more items than maxItems
  const getDisplayBreadcrumb = () => {
    if (breadcrumb.length <= maxItems) {
      return breadcrumb
    }

    // Show first item, ellipsis, and last (maxItems - 2) items
    const firstItem = breadcrumb[0]
    const lastItems = breadcrumb.slice(-(maxItems - 2))

    return [
      firstItem,
      { id: 'ellipsis', title: '...', children: [] } as ConceptNode,
      ...lastItems
    ]
  }

  const displayBreadcrumb = getDisplayBreadcrumb()

  const handleNodeClick = (nodeId: string) => {
    if (nodeId !== 'ellipsis') {
      // This will be handled by the parent component
      // We'll integrate with the store's navigation
    }
  }

  return (
    <div className={`flex items-center gap-2 text-sm ${className}`}>
      {/* Navigation Buttons */}
      {showNavigationButtons && (
        <div className="flex items-center gap-1 mr-4">
          <button
            onClick={navigateBack}
            disabled={!canNavigateBack}
            className={`p-1.5 rounded-md transition-colors ${
              canNavigateBack
                ? 'hover:bg-gray-100 text-gray-700 hover:text-gray-900'
                : 'text-gray-300 cursor-not-allowed'
            }`}
            title="Indietro"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <button
            onClick={navigateForward}
            disabled={!canNavigateForward}
            className={`p-1.5 rounded-md transition-colors ${
              canNavigateForward
                ? 'hover:bg-gray-100 text-gray-700 hover:text-gray-900'
                : 'text-gray-300 cursor-not-allowed'
            }`}
            title="Avanti"
          >
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Breadcrumb Items */}
      <div className="flex items-center gap-1 overflow-hidden">
        <AnimatePresence mode="popLayout">
          {displayBreadcrumb.map((node, index) => (
            <React.Fragment key={node.id}>
              {/* Breadcrumb Item */}
              {node.id === 'ellipsis' ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex items-center px-2 py-1 text-gray-500"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </motion.div>
              ) : (
                <motion.button
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  onClick={() => handleNodeClick(node.id)}
                  className={`flex items-center gap-1 px-2 py-1 rounded-md transition-colors ${
                    node.id === selectedNodeId
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                  }`}
                  title={node.title}
                >
                  {/* Icon for different levels */}
                  {index === 0 && rootNode?.id === node.id && (
                    <Home className="h-3.5 w-3.5" />
                  )}
                  {index === 1 && rootNode?.id !== node.id && (
                    <BookOpen className="h-3.5 w-3.5" />
                  )}

                  {/* Node Title */}
                  <span className="truncate max-w-32">
                    {node.title}
                  </span>

                  {/* Node metadata badges */}
                  <div className="flex items-center gap-1 ml-1">
                    {node.visited && (
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                    )}
                    {node.bookmarked && (
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                    )}
                    {node.masteryLevel !== undefined && (
                      <div
                        className={`w-1.5 h-1.5 rounded-full ${
                          node.masteryLevel >= 80 ? 'bg-green-500' :
                          node.masteryLevel >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                      />
                    )}
                  </div>
                </motion.button>
              )}

              {/* Separator */}
              {index < displayBreadcrumb.length - 1 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center text-gray-400 mx-1"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </motion.div>
              )}
            </React.Fragment>
          ))}
        </AnimatePresence>
      </div>

      {/* Current Path Info */}
      {selectedNodeId && (
        <div className="ml-auto text-xs text-gray-500">
          Livello {breadcrumb.findIndex(n => n.id === selectedNodeId) + 1} di {breadcrumb.length}
        </div>
      )}
    </div>
  )
}

// Compact version for small spaces
export function CompactBreadcrumb({ className = '' }: { className?: string }) {
  const { breadcrumb, selectedNodeId } = useConceptMapStore()

  const currentNode = breadcrumb.find(n => n.id === selectedNodeId)

  return (
    <div className={`flex items-center gap-2 text-xs text-gray-600 ${className}`}>
      {breadcrumb.length > 0 && (
        <>
          <span className="truncate max-w-24">
            {breadcrumb[0].title}
          </span>
          <ChevronRight className="h-3 w-3 flex-shrink-0" />
        </>
      )}
      {currentNode && (
        <span className="font-medium text-gray-900 truncate max-w-32">
          {currentNode.title}
        </span>
      )}
    </div>
  )
}

// Breadcrumb with search/filter functionality
export function SearchableBreadcrumb({ className = '' }: { className?: string }) {
  const { breadcrumb, searchQuery, searchResults, selectedNodeId } = useConceptMapStore()

  const isSearching = searchQuery.trim() !== ''
  const currentPath = breadcrumb.map(n => n.title).join(' > ')

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Current path when searching */}
      {isSearching && (
        <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded-md px-2 py-1">
          Path: {currentPath}
        </div>
      )}

      {/* Search results indicator */}
      {isSearching && (
        <div className="text-xs text-blue-600 bg-blue-50 border border-blue-200 rounded-md px-2 py-1">
          {searchResults.length} risultati per "{searchQuery}"
        </div>
      )}

      {/* Regular breadcrumb */}
      <BreadcrumbNavigation className={isSearching ? 'opacity-50' : ''} />
    </div>
  )
}

// Breadcrumb with context menu for navigation history
export function NavigationBreadcrumb({ className = '' }: { className?: string }) {
  const {
    breadcrumb,
    navigationHistory,
    historyIndex,
    navigateBack,
    navigateForward
  } = useConceptMapStore()

  return (
    <div className={`flex items-center justify-between ${className}`}>
      <BreadcrumbNavigation showNavigationButtons={false} />

      {/* Navigation history indicator */}
      {navigationHistory.length > 1 && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>
            {historyIndex + 1} / {navigationHistory.length}
          </span>
          <div className="flex gap-1">
            <button
              onClick={navigateBack}
              disabled={historyIndex <= 0}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ArrowLeft className="h-3 w-3" />
            </button>
            <button
              onClick={navigateForward}
              disabled={historyIndex >= navigationHistory.length - 1}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}