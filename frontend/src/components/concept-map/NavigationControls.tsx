/**
 * Navigation Controls and Keyboard Shortcuts for Concept Maps
 * Provides comprehensive navigation and control features
 */

'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Settings,
  Download,
  Share2,
  HelpCircle,
  Keyboard,
  Bookmark,
  BookmarkCheck,
  Home,
  Target,
  Eye,
  EyeOff,
  Layers,
  Grid3X3,
  List,
  ChevronDown,
  X
} from 'lucide-react'
import { useConceptMapStore } from '@/stores/conceptMapStore'

interface NavigationControlsProps {
  className?: string
  showShortcuts?: boolean
  onExport?: () => void
  onShare?: () => void
  onToggleSettings?: () => void
}

interface KeyboardShortcut {
  key: string
  description: string
  category: 'navigation' | 'view' | 'interaction' | 'search'
  action: () => void
}

export function NavigationControls({
  className = '',
  showShortcuts = true,
  onExport,
  onShare,
  onToggleSettings
}: NavigationControlsProps) {
  const [showShortcutHelp, setShowShortcutHelp] = useState(false)
  const [searchVisible, setSearchVisible] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const searchInputRef = useRef<HTMLInputElement>(null)

  const {
    zoom,
    setZoom,
    panOffset,
    setPanOffset,
    centerView,
    viewMode,
    setViewMode,
    selectedNodeId,
    breadcrumb,
    navigateBack,
    navigateForward,
    expandedNodes,
    expandAll,
    collapseAll,
    searchNodes,
    clearSearch,
    searchResults,
    showProgressIndicators,
    showAIHints,
    bookmarkedNodes,
    toggleBookmark
  } = useConceptMapStore()

  // Define keyboard shortcuts
  const shortcuts: KeyboardShortcut[] = [
    // Navigation
    {
      key: 'Ctrl + ←',
      description: 'Nodo precedente',
      category: 'navigation',
      action: navigateBack
    },
    {
      key: 'Ctrl + →',
      description: 'Nodo successivo',
      category: 'navigation',
      action: navigateForward
    },
    {
      key: 'Home',
      description: 'Torna alla radice',
      category: 'navigation',
      action: () => {
        if (breadcrumb.length > 0) {
          // Navigate to root node
        }
      }
    },
    {
      key: 'Enter',
      description: 'Espandi/Comprimi nodo',
      category: 'interaction',
      action: () => {
        if (selectedNodeId) {
          // Toggle expansion
        }
      }
    },
    {
      key: 'Space',
      description: 'Centra vista',
      category: 'view',
      action: centerView
    },

    // View controls
    {
      key: 'Ctrl + +',
      description: 'Zoom avanti',
      category: 'view',
      action: () => setZoom(Math.min(zoom + 0.2, 3))
    },
    {
      key: 'Ctrl + -',
      description: 'Zoom indietro',
      category: 'view',
      action: () => setZoom(Math.max(zoom - 0.2, 0.3))
    },
    {
      key: 'Ctrl + 0',
      description: 'Reset zoom',
      category: 'view',
      action: () => {
        setZoom(1)
        setPanOffset({ x: 0, y: 0 })
      }
    },
    {
      key: 'V',
      description: 'Cambia modalità vista',
      category: 'view',
      action: () => {
        const modes: Array<'visual' | 'explorer' | 'both'> = ['visual', 'explorer', 'both']
        const currentIndex = modes.indexOf(viewMode)
        const nextMode = modes[(currentIndex + 1) % modes.length]
        setViewMode(nextMode)
      }
    },

    // Search
    {
      key: 'Ctrl + F',
      description: 'Cerca',
      category: 'search',
      action: () => {
        setSearchVisible(true)
        setTimeout(() => searchInputRef.current?.focus(), 100)
      }
    },
    {
      key: 'Esc',
      description: 'Chiudi cerca/aiuto',
      category: 'search',
      action: () => {
        setSearchVisible(false)
        setShowShortcutHelp(false)
        clearSearch()
      }
    },
    {
      key: 'F3',
      description: 'Prossimo risultato',
      category: 'search',
      action: () => {
        // Navigate to next search result
      }
    },

    // Interaction
    {
      key: 'E',
      description: 'Espandi tutto',
      category: 'interaction',
      action: expandAll
    },
    {
      key: 'W',
      description: 'Comprimi tutto',
      category: 'interaction',
      action: collapseAll
    },
    {
      key: 'B',
      description: 'Toggle bookmark',
      category: 'interaction',
      action: () => {
        if (selectedNodeId) {
          toggleBookmark(selectedNodeId)
        }
      }
    },
    {
      key: 'P',
      description: 'Toggle progress',
      category: 'interaction',
      action: () => {
        // Toggle progress indicators
      }
    },
    {
      key: 'H',
      description: 'Toggle AI hints',
      category: 'interaction',
      action: () => {
        // Toggle AI hints
      }
    },

    // Help
    {
      key: 'F1',
      description: 'Mostra aiuto',
      category: 'search',
      action: () => setShowShortcutHelp(true)
    },
    {
      key: '?',
      description: 'Mostra scorciatoie',
      category: 'search',
      action: () => setShowShortcutHelp(true)
    }
  ]

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Find matching shortcut
    const keyCombo = []
    if (event.ctrlKey) keyCombo.push('Ctrl')
    if (event.altKey) keyCombo.push('Alt')
    if (event.shiftKey) keyCombo.push('Shift')
    keyCombo.push(event.key)

    const keyString = keyCombo.join(' + ')

    const matchingShortcut = shortcuts.find(shortcut => {
      const shortcutKeys = shortcut.key.toLowerCase().split(' + ')
      const eventKeys = keyString.toLowerCase().split(' + ')
      return shortcutKeys.every(key => eventKeys.includes(key.toLowerCase()))
    })

    if (matchingShortcut) {
      event.preventDefault()
      matchingShortcut.action()
    }
  }, [shortcuts, selectedNodeId])

  // Set up keyboard event listeners
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (query.trim()) {
      searchNodes(query)
    } else {
      clearSearch()
    }
  }

  const isBookmarked = selectedNodeId ? bookmarkedNodes.has(selectedNodeId) : false

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Search */}
      <AnimatePresence>
        {searchVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, width: 0 }}
            animate={{ opacity: 1, scale: 1, width: 'auto' }}
            exit={{ opacity: 0, scale: 0.95, width: 0 }}
            className="relative"
          >
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Cerca concetti..."
              className="w-64 px-3 py-2 pl-10 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <button
              onClick={() => {
                setSearchVisible(false)
                clearSearch()
              }}
              className="absolute right-2 top-2.5 p-1 rounded-md hover:bg-gray-100"
            >
              <X className="h-4 w-4 text-gray-400" />
            </button>

            {/* Search results dropdown */}
            {searchResults.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto z-50"
              >
                {searchResults.slice(0, 5).map(nodeId => (
                  <div
                    key={nodeId}
                    className="px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm"
                  >
                    {/* Search result item */}
                  </div>
                ))}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search button when not visible */}
      {!searchVisible && (
        <button
          onClick={() => setSearchVisible(true)}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title="Cerca (Ctrl+F)"
        >
          <Search className="h-4 w-4 text-gray-600" />
        </button>
      )}

      {/* View Mode Toggle */}
      <div className="flex items-center bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setViewMode('visual')}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'visual'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          title="Modalità visuale"
        >
          <Grid3X3 className="h-4 w-4" />
        </button>
        <button
          onClick={() => setViewMode('explorer')}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'explorer'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          title="Modalità esplorazione"
        >
          <List className="h-4 w-4" />
        </button>
        <button
          onClick={() => setViewMode('both')}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'both'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          title="Entrambe le visualizzazioni"
        >
          <Layers className="h-4 w-4" />
        </button>
      </div>

      {/* Zoom Controls */}
      <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setZoom(Math.max(zoom - 0.2, 0.3))}
          className="p-1.5 rounded-md hover:bg-white transition-colors"
          title="Zoom indietro (Ctrl+-)"
        >
          <ZoomOut className="h-4 w-4 text-gray-600" />
        </button>
        <span className="px-2 text-xs text-gray-600 min-w-[3rem] text-center">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
          className="p-1.5 rounded-md hover:bg-white transition-colors"
          title="Zoom avanti (Ctrl++)"
        >
          <ZoomIn className="h-4 w-4 text-gray-600" />
        </button>
        <button
          onClick={centerView}
          className="p-1.5 rounded-md hover:bg-white transition-colors"
          title="Centra vista (Spazio)"
        >
          <Maximize2 className="h-4 w-4 text-gray-600" />
        </button>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center gap-1">
        <button
          onClick={navigateBack}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Indietro (Ctrl+←)"
        >
          <ChevronDown className="h-4 w-4 text-gray-600 rotate-90" />
        </button>
        <button
          onClick={navigateForward}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Avanti (Ctrl+→)"
        >
          <ChevronDown className="h-4 w-4 text-gray-600 -rotate-90" />
        </button>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => selectedNodeId && toggleBookmark(selectedNodeId)}
          disabled={!selectedNodeId}
          className={`p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
            isBookmarked
              ? 'bg-blue-100 text-blue-600'
              : 'hover:bg-gray-100 text-gray-600'
          }`}
          title="Toggle bookmark (B)"
        >
          {isBookmarked ? (
            <BookmarkCheck className="h-4 w-4" />
          ) : (
            <Bookmark className="h-4 w-4" />
          )}
        </button>

        <button
          onClick={expandAll}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title="Espandi tutto (E)"
        >
          <Eye className="h-4 w-4 text-gray-600" />
        </button>

        <button
          onClick={collapseAll}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title="Comprimi tutto (W)"
        >
          <EyeOff className="h-4 w-4 text-gray-600" />
        </button>
      </div>

      {/* Tools */}
      <div className="flex items-center gap-1 border-l border-gray-200 pl-2">
        {showShortcuts && (
          <button
            onClick={() => setShowShortcutHelp(true)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Mostra scorciatoie (F1)"
          >
            <Keyboard className="h-4 w-4 text-gray-600" />
          </button>
        )}

        {onExport && (
          <button
            onClick={onExport}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Esporta"
          >
            <Download className="h-4 w-4 text-gray-600" />
          </button>
        )}

        {onShare && (
          <button
            onClick={onShare}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Condividi"
          >
            <Share2 className="h-4 w-4 text-gray-600" />
          </button>
        )}

        {onToggleSettings && (
          <button
            onClick={onToggleSettings}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Impostazioni"
          >
            <Settings className="h-4 w-4 text-gray-600" />
          </button>
        )}
      </div>

      {/* Keyboard Shortcuts Help Modal */}
      <AnimatePresence>
        {showShortcutHelp && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowShortcutHelp(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden m-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">Scorciatoie da Tastiera</h2>
                  <button
                    onClick={() => setShowShortcutHelp(false)}
                    className="p-2 rounded-md hover:bg-gray-100"
                  >
                    <X className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              </div>

              <div className="p-6 overflow-y-auto max-h-[60vh]">
                {['navigation', 'view', 'interaction', 'search'].map(category => (
                  <div key={category} className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-900 mb-3 capitalize">
                      {category === 'navigation' && 'Navigazione'}
                      {category === 'view' && 'Vista'}
                      {category === 'interaction' && 'Interazione'}
                      {category === 'search' && 'Ricerca'}
                    </h3>
                    <div className="space-y-2">
                      {shortcuts
                        .filter(shortcut => shortcut.category === category)
                        .map((shortcut, index) => (
                          <div key={index} className="flex items-center justify-between py-2">
                            <span className="text-sm text-gray-600">{shortcut.description}</span>
                            <kbd className="px-2 py-1 text-xs bg-gray-100 border border-gray-200 rounded">
                              {shortcut.key}
                            </kbd>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-6 border-t border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Premi <kbd className="px-2 py-1 text-xs bg-gray-100 border border-gray-200 rounded">Esc</kbd> per chiudere
                  </p>
                  <button
                    onClick={() => setShowShortcutHelp(false)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Chiudi
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Compact version for smaller spaces
export function CompactNavigationControls({ className = '' }: { className?: string }) {
  const [showMore, setShowMore] = useState(false)

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <NavigationControls
        showShortcuts={false}
        className="hidden md:flex"
      />

      <button
        onClick={() => setShowMore(!showMore)}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors md:hidden"
      >
        <Settings className="h-4 w-4 text-gray-600" />
      </button>
    </div>
  )
}