/**
 * Custom Highlight Components
 * Componenti personalizzati per evidenziare testo nei PDF senza dipendenze esterne
 */

'use client'

import React from 'react'

export interface HighlightPosition {
  x: number
  y: number
  width: number
  height: number
  pageNumber: number
}

export interface CustomHighlightProps {
  id: string
  position: HighlightPosition
  content: { text: string; image?: string }
  comment: { emoji: string; text: string }
  color: string
  type: 'highlight' | 'underline' | 'note'
  isScrolledTo?: boolean
  onClick?: () => void
  onMouseOver?: () => void
  onMouseOut?: () => void
}

export const CustomHighlight: React.FC<CustomHighlightProps> = ({
  id,
  position,
  content,
  comment,
  color,
  type,
  isScrolledTo = false,
  onClick,
  onMouseOver,
  onMouseOut
}) => {
  const baseClasses = "absolute cursor-pointer transition-all duration-200 hover:opacity-80"
  const style: React.CSSProperties = {
    left: position.x,
    top: position.y,
    width: position.width,
    height: position.height,
    backgroundColor: type === 'highlight' ? color : 'transparent',
    borderBottom: type === 'underline' ? `2px solid ${color}` : 'none',
    borderRadius: type === 'highlight' ? '2px' : '0',
    zIndex: 10,
    pointerEvents: 'auto'
  }

  return (
    <div
      key={id}
      className={`${baseClasses} ${isScrolledTo ? 'ring-2 ring-blue-500' : ''}`}
      style={style}
      title={comment.text || content.text}
      onClick={onClick}
      onMouseOver={onMouseOver}
      onMouseOut={onMouseOut}
      data-highlight-id={id}
    >
      {type === 'note' && (
        <div
          className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full hover:bg-yellow-500 transition-colors"
          title={comment.text || 'Nota'}
        />
      )}
      {comment.text && (
        <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          {comment.emoji} {comment.text}
        </div>
      )}
    </div>
  )
}

export default CustomHighlight