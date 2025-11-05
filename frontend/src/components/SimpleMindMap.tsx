'use client'

import { useState, useEffect } from 'react'

interface MindMapNode {
  id: string
  text: string
  level: number
  children: MindMapNode[]
}

interface SimpleMindMapProps {
  content: string
}

export default function SimpleMindMap({ content }: SimpleMindMapProps) {
  const [mindMapData, setMindMapData] = useState<{ title: string; nodes: MindMapNode[] } | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  useEffect(() => {
    const parseMindMapFromText = (text: string) => {
      let markdownContent = text

      // Look for ```markdown wrapper
      const markdownMatch = text.match(/```markdown\n([\s\S]*?)\n```/)
      if (markdownMatch) {
        markdownContent = markdownMatch[1]
      }

      const lines = markdownContent.split('\n').filter(line => line.trim())
      const nodes: MindMapNode[] = []
      const stack: { node: MindMapNode; level: number }[] = []

      let title = 'Mappa Concettuale'
      let nodeIndex = 0

      lines.forEach((line) => {
        const trimmedLine = line.trim()

        // Extract title
        if (trimmedLine.startsWith('# ')) {
          title = trimmedLine.substring(2).trim()
          return
        }

        // Parse headers as nodes
        const match = trimmedLine.match(/^(#{2,3}) (.+)$/)
        if (match) {
          const level = match[1].length
          const text = match[2].trim()

          const node: MindMapNode = {
            id: `node-${nodeIndex++}`,
            text,
            level,
            children: []
          }

          // Remove nodes from stack that are at the same or deeper level
          while (stack.length > 0 && stack[stack.length - 1].level >= level) {
            stack.pop()
          }

          // Add as child to parent if exists
          if (stack.length > 0) {
            stack[stack.length - 1].node.children.push(node)
          } else {
            nodes.push(node)
          }

          stack.push({ node, level })
        } else if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
          // Handle bullet points
          const bulletText = trimmedLine.substring(2).trim()
          if (stack.length > 0) {
            const bulletNode: MindMapNode = {
              id: `bullet-${nodeIndex++}`,
              text: bulletText,
              level: stack[stack.length - 1].level + 1,
              children: []
            }
            stack[stack.length - 1].node.children.push(bulletNode)
          }
        }
      })

      // Create default structure if no nodes found
      if (nodes.length === 0) {
        const defaultNode: MindMapNode = {
          id: 'node-default',
          text: title || 'Mappa Concettuale',
          level: 2,
          children: [
            {
              id: 'node-child-1',
              text: 'Concetto Principale 1',
              level: 3,
              children: [
                {
                  id: 'node-grandchild-1',
                  text: 'Dettaglio 1.1',
                  level: 4,
                  children: []
                },
                {
                  id: 'node-grandchild-2',
                  text: 'Dettaglio 1.2',
                  level: 4,
                  children: []
                }
              ]
            },
            {
              id: 'node-child-2',
              text: 'Concetto Principale 2',
              level: 3,
              children: [
                {
                  id: 'node-grandchild-3',
                  text: 'Dettaglio 2.1',
                  level: 4,
                  children: []
                }
              ]
            },
            {
              id: 'node-child-3',
              text: 'Concetto Principale 3',
              level: 3,
              children: []
            }
          ]
        }
        nodes.push(defaultNode)
      }

      return { title, nodes }
    }

    const data = parseMindMapFromText(content)
    setMindMapData(data)

    // Expand all nodes by default
    const allNodeIds = new Set<string>()
    const collectNodeIds = (nodes: MindMapNode[]) => {
      nodes.forEach(node => {
        allNodeIds.add(node.id)
        collectNodeIds(node.children)
      })
    }
    collectNodeIds(data.nodes)
    setExpandedNodes(allNodeIds)
  }, [content])

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const getNodeColor = (level: number) => {
    const colors = [
      'bg-purple-500',
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-pink-500'
    ]
    return colors[(level - 2) % colors.length] || colors[0]
  }

  const renderNode = (node: MindMapNode, depth: number = 0) => {
    const isExpanded = expandedNodes.has(node.id)
    const hasChildren = node.children.length > 0
    const colorClass = getNodeColor(node.level)
    const marginLeft = depth * 24

    return (
      <div key={node.id} className="select-none">
        <div className="flex items-center mb-2" style={{ marginLeft: `${marginLeft}px` }}>
          {/* Connection line */}
          {depth > 0 && (
            <div className="w-6 h-px bg-gray-300 mr-2"></div>
          )}

          {/* Node */}
          <div
            className={`flex items-center px-3 py-2 rounded-lg text-white text-sm font-medium shadow-sm hover:shadow-md transition-shadow cursor-pointer ${colorClass}`}
            onClick={() => hasChildren && toggleNode(node.id)}
          >
            {hasChildren && (
              <span className="mr-2 text-xs">
                {isExpanded ? '−' : '+'}
              </span>
            )}
            <span className="truncate max-w-xs">
              {node.text}
            </span>
          </div>
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="relative">
            {/* Vertical connection line */}
            <div
              className="absolute w-px bg-gray-300"
              style={{
                left: `${marginLeft + 12}px`,
                top: '0px',
                bottom: '8px'
              }}
            ></div>
            {node.children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (!mindMapData) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6 bg-gray-50 rounded-lg overflow-auto max-h-96">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
        {mindMapData.title}
      </h3>
      <div className="flex justify-center">
        <div className="inline-block">
          {mindMapData.nodes.map(node => renderNode(node))}
        </div>
      </div>
    </div>
  )
}