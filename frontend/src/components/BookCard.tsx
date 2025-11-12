'use client'

import type { MouseEvent } from 'react'
import Link from 'next/link'
import { BookOpen, FileText, Clock, Trash2, Brain, MessageCircle, Play, Eye } from 'lucide-react'
import { fetchFromBackend } from '@/lib/api'

interface BookChapter {
  title: string
  summary: string
  estimated_minutes: number | null
}

interface Book {
  id: string
  title: string
  author: string
  description: string
  year: string
  publisher: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
  chapters: BookChapter[]
  tags: string[]
}

interface BookCardProps {
  book: Book
  courseId: string
  onDelete?: (bookId: string) => void
}

export default function BookCard({ book, courseId, onDelete }: BookCardProps) {
  const handleDelete = async (event: MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    if (!confirm('Sei sicuro di voler eliminare questo libro?')) {
      return
    }

    try {
      const response = await fetchFromBackend(`/api/courses/${courseId}/books/${book.id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        onDelete?.(book.id)
      } else {
        alert('Errore durante l\'eliminazione del libro')
      }
    } catch {
      alert('Errore durante l\'eliminazione del libro')
    }
  }

  const totalEstimatedMinutes = book.chapters
    ? book.chapters.reduce((acc, chapter) => acc + (chapter.estimated_minutes || 0), 0)
    : 0

  const handleCardClick = () => {
    window.location.href = `/courses/${courseId}/books/${book.id}`
  }

  return (
    <div
      onClick={handleCardClick}
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 hover:border-blue-300 cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
            <BookOpen className="h-6 w-6 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
              {book.title}
            </h3>
            <p className="text-sm text-gray-600">{book.author}</p>
          </div>
        </div>

        <button
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-all duration-200"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {book.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {book.description}
        </p>
      )}

      {book.chapters && book.chapters.length > 0 && (
        <div className="text-xs text-gray-500 mb-4">
          {book.chapters.length} capitol{book.chapters.length === 1 ? 'o' : 'i'}
          {totalEstimatedMinutes > 0 && (
            <span> • {totalEstimatedMinutes} minuti consigliati</span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <span>{book.year} • {book.publisher}</span>
        {book.materials_count > 0 && (
          <div className="flex items-center space-x-1">
            <FileText className="h-4 w-4" />
            <span>{book.materials_count} material{book.materials_count !== 1 ? 'i' : ''}</span>
          </div>
        )}
      </div>

      {book.tags && book.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {book.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
          {book.tags.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              +{book.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {book.materials_count > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          <Link
            href={`/courses/${courseId}/study?book=${book.id}`}
            className="inline-flex items-center px-3 py-1.5 bg-green-100 text-green-700 text-xs font-medium rounded-lg hover:bg-green-200 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <Play className="h-3 w-3 mr-1" />
            Read & Study
          </Link>
          <Link
            href={`/courses/${courseId}/books/${book.id}/mindmap`}
            className="inline-flex items-center px-3 py-1.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-lg hover:bg-purple-200 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <Brain className="h-3 w-3 mr-1" />
            Mindmap
          </Link>
          <Link
            href={`/chat?course=${courseId}&book=${book.id}`}
            className="inline-flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-lg hover:bg-blue-200 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <MessageCircle className="h-3 w-3 mr-1" />
            Chat Tutor
          </Link>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          {book.study_sessions > 0 && (
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{book.study_sessions} session{book.study_sessions !== 1 ? 'i' : ''}</span>
            </div>
          )}
          {book.total_study_time > 0 && (
            <span>{Math.round(book.total_study_time / 60)}h</span>
          )}
        </div>
        <Link
          href={`/courses/${courseId}/books/${book.id}#materials`}
          className="text-blue-600 hover:text-blue-700 font-medium"
          onClick={(e) => e.stopPropagation()}
        >
          Vedi dettagli →
        </Link>
      </div>
    </div>
  )
}
