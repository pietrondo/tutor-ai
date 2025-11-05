'use client'

import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, Sparkles, Lightbulb, CheckCircle2, Flag, GitBranch } from 'lucide-react'
import { StudyMindmap, StudyMindmapNode, StudyPlanPhase } from '@/types/mindmap'

interface MindmapExplorerProps {
  mindmap: StudyMindmap
  onExpandNode?: (path: StudyMindmapNode[]) => Promise<void>
}

export function MindmapExplorer({ mindmap, onExpandNode }: MindmapExplorerProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [loadingNodes, setLoadingNodes] = useState<Set<string>>(new Set())
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  const getPriorityMeta = (priority: number | null | undefined) => {
    if (priority === null || priority === undefined) return null

    if (priority <= 1) {
      return {
        label: 'Priorità alta',
        shortLabel: 'Alta',
        badgeClass: 'bg-red-100 text-red-700 border border-red-200'
      }
    }
    if (priority === 2) {
      return {
        label: 'Priorità media',
        shortLabel: 'Media',
        badgeClass: 'bg-amber-100 text-amber-700 border border-amber-200'
      }
    }
    if (priority === 3) {
      return {
        label: 'Priorità medio-bassa',
        shortLabel: 'Medio-bassa',
        badgeClass: 'bg-yellow-50 text-yellow-700 border border-yellow-200'
      }
    }
    return {
      label: 'Priorità bassa',
      shortLabel: 'Bassa',
      badgeClass: 'bg-slate-100 text-slate-600 border border-slate-200'
    }
  }

  const renderPriorityBadge = (priority: number | null | undefined) => {
    const meta = getPriorityMeta(priority)
    if (!meta) return null
    return (
      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${meta.badgeClass}`}>
        {meta.shortLabel}
      </span>
    )
  }

  useEffect(() => {
    // Expand root nodes on load
    const nextExpanded = new Set<string>()
    mindmap.nodes.forEach((node) => nextExpanded.add(node.id))
    setExpandedNodes(nextExpanded)

    if (mindmap.nodes.length > 0) {
      setSelectedNodeId(mindmap.nodes[0].id)
    } else {
      setSelectedNodeId(null)
    }
  }, [mindmap])

  const findNodeById = (nodes: StudyMindmapNode[], id: string | null): StudyMindmapNode | null => {
    if (!id) return null
    for (const node of nodes) {
      if (node.id === id) return node
      const child = findNodeById(node.children, id)
      if (child) return child
    }
    return null
  }

  const selectedNode = useMemo(
    () => findNodeById(mindmap.nodes, selectedNodeId),
    [mindmap.nodes, selectedNodeId]
  )

  const selectedPriorityMeta = selectedNode ? getPriorityMeta(selectedNode.priority) : null

  const findPathById = (nodes: StudyMindmapNode[], id: string | null, path: StudyMindmapNode[] = []): StudyMindmapNode[] => {
    if (!id) return []
    for (const node of nodes) {
      const nextPath = [...path, node]
      if (node.id === id) return nextPath
      const childPath = findPathById(node.children, id, nextPath)
      if (childPath.length > 0) return childPath
    }
    return []
  }

  const selectedPath = useMemo(
    () => findPathById(mindmap.nodes, selectedNodeId),
    [mindmap.nodes, selectedNodeId]
  )

  const toggleNode = (nodeId: string) => {
    const updated = new Set(expandedNodes)
    if (updated.has(nodeId)) {
      updated.delete(nodeId)
    } else {
      updated.add(nodeId)
    }
    setExpandedNodes(updated)
  }

  const handleExpand = async (path: StudyMindmapNode[]) => {
    if (!onExpandNode) return
    const node = path[path.length - 1]
    if (!node) return

    const nextLoading = new Set(loadingNodes)
    nextLoading.add(node.id)
    setLoadingNodes(nextLoading)

    try {
      await onExpandNode(path)
      setExpandedNodes((prev) => new Set(prev).add(node.id))
    } finally {
      setLoadingNodes((prev) => {
        const updated = new Set(prev)
        updated.delete(node.id)
        return updated
      })
    }
  }

  const renderNode = (node: StudyMindmapNode, depth: number, path: StudyMindmapNode[]) => {
    const isExpanded = expandedNodes.has(node.id)
    const hasChildren = node.children.length > 0
    const isLoading = loadingNodes.has(node.id)

    const nodePath = [...path, node]

    return (
      <div key={node.id} className="mb-2">
        <div className="flex items-start gap-2">
          <button
            onClick={() => toggleNode(node.id)}
            className="mt-1 text-gray-500 hover:text-gray-700 transition-colors"
            aria-label={isExpanded ? 'Comprimi nodo' : 'Espandi nodo'}
          >
            {hasChildren || onExpandNode ? (
              isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
            ) : (
              <span className="inline-block w-4" />
            )}
          </button>
          <div
            onClick={() => setSelectedNodeId(node.id)}
            className={`flex-1 p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedNodeId === node.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="font-semibold text-gray-900">{node.title}</div>
                  {renderPriorityBadge(node.priority)}
                </div>
                {node.summary && <div className="text-sm text-gray-600 mt-1">{node.summary}</div>}
                {node.study_actions.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    <span className="font-medium text-gray-700">Attività:</span>{' '}
                    {node.study_actions.slice(0, 2).join('; ')}
                    {node.study_actions.length > 2 && '…'}
                  </div>
                )}
                <div className="mt-2 flex items-center gap-1 text-[11px] text-gray-500">
                  <GitBranch className="h-3 w-3" />
                  <span>{node.children.length} sotto-concetti collegati</span>
                </div>
              </div>
              {onExpandNode && (
                <button
                  onClick={(event) => {
                    event.stopPropagation()
                    handleExpand(nodePath)
                  }}
                  className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-purple-100 text-purple-700 hover:bg-purple-200 transition-colors"
                >
                  {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                  <span>Espandi</span>
                </button>
              )}
            </div>
          </div>
        </div>
        {isExpanded && (hasChildren || isLoading) && (
          <div className="ml-6 mt-2 border-l border-gray-200 pl-4">
            {node.children.map((child) => renderNode(child, depth + 1, nodePath))}
            {isLoading && (
              <div className="flex items-center gap-2 text-sm text-purple-600 mt-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Generazione con l'AI in corso…
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderStudyPlan = (plan: StudyPlanPhase[]) => {
    if (!plan.length) return null

    return (
      <div className="mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Piano di studio guidato</h3>
        <div className="space-y-3">
          {plan.map((phase, index) => (
            <div key={`${phase.phase}-${index}`} className="border border-blue-100 bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-700 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                {phase.phase}
              </div>
              {phase.objective && <div className="mt-2 text-sm text-gray-700">Obiettivo: {phase.objective}</div>}
              {phase.activities.length > 0 && (
                <ul className="mt-2 text-sm text-gray-700 list-disc list-inside space-y-1">
                  {phase.activities.map((activity, idx) => (
                    <li key={idx}>{activity}</li>
                  ))}
                </ul>
              )}
              {phase.ai_support && (
                <div className="mt-2 text-xs text-purple-700 bg-purple-100 inline-flex items-center gap-1 px-2 py-1 rounded">
                  <Lightbulb className="h-3 w-3" />
                  {phase.ai_support}
                </div>
              )}
              {phase.duration_minutes && (
                <div className="mt-2 text-xs text-gray-500">
                  Durata suggerita: {phase.duration_minutes} minuti
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
      <div className="lg:col-span-3">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">{mindmap.title}</h3>
        {mindmap.overview && <p className="text-gray-600 mb-6">{mindmap.overview}</p>}
        <div className="bg-white border border-gray-200 rounded-xl p-4 max-h-[600px] overflow-auto">
          {mindmap.nodes.map((node) => renderNode(node, 0, []))}
        </div>
      </div>
      <div className="lg:col-span-2">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          {selectedNode ? (
            <>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">{selectedNode.title}</h4>
              {selectedPriorityMeta && (
                <div className="mb-3 flex items-center gap-2 text-xs text-gray-600">
                  <Flag className="h-3 w-3 text-amber-600" />
                  <span className="font-semibold text-gray-700">Priorità:</span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${selectedPriorityMeta.badgeClass}`}
                  >
                    {selectedPriorityMeta.shortLabel}
                  </span>
                </div>
              )}
              {selectedPath.length > 1 && (
                <div className="mb-4 text-xs text-gray-500 flex items-center gap-2">
                  <GitBranch className="h-3 w-3" />
                  <span>{selectedPath.map((node) => node.title).join(' > ')}</span>
                </div>
              )}
              {selectedNode.summary && (
                <p className="text-sm text-gray-700 mb-4">{selectedNode.summary}</p>
              )}
              {selectedNode.study_actions.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm font-semibold text-gray-800 mb-2">Attività suggerite</h5>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                    {selectedNode.study_actions.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedNode.ai_hint && (
                <div className="mb-4 text-sm text-purple-700 bg-purple-50 border border-purple-100 px-3 py-2 rounded-lg flex items-start gap-2">
                  <Sparkles className="h-4 w-4 mt-0.5" />
                  <div>
                    <div className="font-semibold">Suggerimento AI</div>
                    <p>{selectedNode.ai_hint}</p>
                  </div>
                </div>
              )}
              {selectedNode.references && selectedNode.references.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm font-semibold text-gray-800 mb-2">Riferimenti</h5>
                  <div className="flex flex-wrap gap-2">
                    {selectedNode.references.map((reference, index) => (
                      <span
                        key={`${reference}-${index}`}
                        className="px-2 py-1 text-xs rounded-full bg-blue-50 border border-blue-100 text-blue-700"
                      >
                        {reference}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-gray-500 text-sm">Seleziona un nodo per vedere i dettagli</div>
          )}
        </div>
        {renderStudyPlan(mindmap.study_plan)}
        {mindmap.references && mindmap.references.length > 0 && (
          <div className="mt-4 bg-white border border-gray-200 rounded-xl p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Riferimenti globali</h4>
            <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
              {mindmap.references.map((ref, index) => (
                <li key={index}>{ref}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
