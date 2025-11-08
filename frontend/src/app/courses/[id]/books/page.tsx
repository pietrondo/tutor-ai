'use client'

import { useState, useEffect, type FormEvent } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Plus, BookOpen, Search, Filter } from 'lucide-react'
import BookCard from '@/components/BookCard'
import { fetchFromBackend } from '@/lib/api'

interface BookChapter {
  title: string
  summary: string
  estimated_minutes: number | null
  topics: string[]
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

const toStringValue = (value: unknown): string => {
  if (typeof value === 'string') {
    return value
  }
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
}

const toFiniteNumber = (value: unknown): number => {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

const normalizeChapter = (chapter: unknown): BookChapter | null => {
  if (typeof chapter === 'string') {
    const title = chapter.trim()
    if (!title) return null
    return {
      title,
      summary: '',
      estimated_minutes: null,
      topics: []
    }
  }

  if (chapter && typeof chapter === 'object') {
    const data = chapter as Record<string, unknown>
    const rawTitle = typeof data.title === 'string' ? data.title : typeof data.name === 'string' ? data.name : ''
    const title = rawTitle.trim()
    if (!title) return null

    let estimated: number | null = null
    if (typeof data.estimated_minutes === 'number') {
      estimated = data.estimated_minutes
    } else if (typeof data.estimated_minutes === 'string' && data.estimated_minutes.trim()) {
      const parsed = Number.parseInt(data.estimated_minutes, 10)
      estimated = Number.isFinite(parsed) && parsed >= 0 ? parsed : null
    }

    return {
      title,
      summary: typeof data.summary === 'string' ? data.summary.trim() : '',
      estimated_minutes: estimated,
      topics: Array.isArray(data.topics) ? data.topics.map(topic => toStringValue(topic)).filter(Boolean) : []
    }
  }

  return null
}

const normalizeBook = (book: unknown): Book => {
  const record = (book && typeof book === 'object') ? book as Record<string, unknown> : {}
  const chaptersArray = Array.isArray(record.chapters) ? record.chapters : []
  const normalizedChapters = chaptersArray
    .map(normalizeChapter)
    .filter((chapter): chapter is BookChapter => Boolean(chapter))

  return {
    id: toStringValue(record.id),
    title: toStringValue(record.title),
    author: toStringValue(record.author),
    description: toStringValue(record.description),
    year: toStringValue(record.year),
    publisher: toStringValue(record.publisher),
    materials_count: toFiniteNumber(record.materials_count),
    study_sessions: toFiniteNumber(record.study_sessions),
    total_study_time: toFiniteNumber(record.total_study_time),
    created_at: toStringValue(record.created_at),
    chapters: normalizedChapters,
    tags: Array.isArray(record.tags) ? record.tags.map(tag => toStringValue(tag)).filter(Boolean) : []
  }
}

export default function BooksPage() {
  const params = useParams()
  const courseId = params.id as string

  const [books, setBooks] = useState<Book[]>([])
  const [courseName, setCourseName] = useState('')
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchBooks()
    fetchCourseInfo()
  }, [courseId])

  const fetchBooks = async () => {
    try {
      const response = await fetchFromBackend(`/api/courses/${courseId}/books`)
      if (response.ok) {
        const data = await response.json()
        const normalized = Array.isArray(data.books) ? data.books.map(normalizeBook) : []
        setBooks(normalized)
      } else {
        setError('Errore nel caricamento dei libri')
      }
    } catch {
      setError('Errore nel caricamento dei libri')
    } finally {
      setLoading(false)
    }
  }

  const fetchCourseInfo = async () => {
    try {
      const response = await fetchFromBackend(`/api/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setCourseName(data.course.name)
      }
    } catch (err) {
      console.error('Error fetching course info:', err)
    }
  }

  const handleBookDelete = (bookId: string) => {
    setBooks(books.filter(book => book.id !== bookId))
  }

  const filteredBooks = books.filter(book =>
    book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    book.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
    book.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    book.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento libri...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container-responsive py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link
              href={`/courses/${courseId}`}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </Link>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">Libri del Corso</h1>
              <p className="text-gray-600 mt-1">{courseName}</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-5 w-5" />
              <span>Aggiungi Libro</span>
            </button>
          </div>

          {/* Search and Filter */}
          <div className="flex items-center space-x-4 bg-white p-4 rounded-lg border">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Cerca per titolo, autore, descrizione o tag..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button className="flex items-center space-x-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
              <Filter className="h-4 w-4" />
              <span>Filtra</span>
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Books Grid */}
        {filteredBooks.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <BookOpen className="h-10 w-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm ? 'Nessun libro trovato' : 'Nessun libro ancora aggiunto'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchTerm
                ? 'Prova a modificare i criteri di ricerca'
                : 'Inizia aggiungendo il primo libro per questo corso'
              }
            </p>
            {!searchTerm && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Aggiungi Libro
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredBooks.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                courseId={courseId}
                onDelete={handleBookDelete}
              />
            ))}
          </div>
        )}

        {/* Stats */}
        {books.length > 0 && (
          <div className="mt-8 bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistiche</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Totale Libri</p>
                <p className="text-2xl font-bold text-gray-900">{books.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Materiali Caricati</p>
                <p className="text-2xl font-bold text-gray-900">
                  {books.reduce((sum, book) => sum + book.materials_count, 0)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Sessioni di Studio</p>
                <p className="text-2xl font-bold text-gray-900">
                  {books.reduce((sum, book) => sum + book.study_sessions, 0)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Tempo Totale</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(books.reduce((sum, book) => sum + book.total_study_time, 0) / 60)}h
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Book Modal */}
      {showCreateModal && (
        <CreateBookModal
          courseId={courseId}
          onClose={() => setShowCreateModal(false)}
          onBookCreated={fetchBooks}
        />
      )}
    </div>
  )
}

// Create Book Modal Component
type ChapterFormState = {
  title: string
  summary: string
  estimated_minutes: string
}

const createEmptyChapter = (): ChapterFormState => ({
  title: '',
  summary: '',
  estimated_minutes: ''
})

function CreateBookModal({ courseId, onClose, onBookCreated }: {
  courseId: string
  onClose: () => void
  onBookCreated: () => void
}) {
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    isbn: '',
    description: '',
    year: '',
    publisher: '',
    chapters: [createEmptyChapter()],
    tags: ['']
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const normalizedChapters = formData.chapters
        .map(chapter => {
          const title = chapter.title.trim()
          if (!title) return null

          let estimatedMinutes: number | null = null
          if (chapter.estimated_minutes.trim()) {
            const parsed = Number.parseInt(chapter.estimated_minutes, 10)
            if (Number.isFinite(parsed) && parsed >= 0) {
              estimatedMinutes = parsed
            }
          }

          return {
            title,
            summary: chapter.summary.trim(),
            estimated_minutes: estimatedMinutes
          }
        })
        .filter((chapter): chapter is { title: string; summary: string; estimated_minutes: number | null } => Boolean(chapter))

      const normalizedTags = Array.from(new Set(formData.tags.map(tag => tag.trim()).filter(tag => tag.length > 0)))

      const bookData = {
        ...formData,
        chapters: normalizedChapters,
        tags: normalizedTags
      }

      const response = await fetchFromBackend(`/api/courses/${courseId}/books`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookData),
      })

      if (response.ok) {
        onBookCreated()
        onClose()
      } else {
        setError('Errore durante la creazione del libro')
      }
    } catch {
      setError('Errore durante la creazione del libro')
    } finally {
      setLoading(false)
    }
  }

  const addChapter = () => {
    setFormData(prev => ({
      ...prev,
      chapters: [...prev.chapters, createEmptyChapter()]
    }))
  }

  const removeChapter = (index: number) => {
    setFormData(prev => ({
      ...prev,
      chapters: prev.chapters.filter((_, i) => i !== index)
    }))
  }

  const addTag = () => {
    setFormData(prev => ({
      ...prev,
      tags: [...prev.tags, '']
    }))
  }

  const removeTag = (index: number) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Nuovo Libro</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Titolo *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Autore
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData(prev => ({ ...prev, author: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ISBN
              </label>
              <input
                type="text"
                value={formData.isbn}
                onChange={(e) => setFormData(prev => ({ ...prev, isbn: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Anno
              </label>
              <input
                type="text"
                value={formData.year}
                onChange={(e) => setFormData(prev => ({ ...prev, year: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Editore
              </label>
              <input
                type="text"
                value={formData.publisher}
                onChange={(e) => setFormData(prev => ({ ...prev, publisher: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descrizione
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Capitoli
              </label>
              <button
                type="button"
                onClick={addChapter}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                + Aggiungi capitolo
              </button>
            </div>
            <div className="space-y-3">
              {formData.chapters.map((chapter, index) => (
                <div key={index} className="rounded-lg border border-gray-200 p-4 space-y-3 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Capitolo {index + 1}</span>
                    {formData.chapters.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeChapter(index)}
                        className="text-xs text-red-500 hover:text-red-700"
                      >
                        Rimuovi
                      </button>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Titolo *
                    </label>
                    <input
                      type="text"
                      value={chapter.title}
                      onChange={(e) => {
                        const newChapters = [...formData.chapters]
                        newChapters[index] = { ...newChapters[index], title: e.target.value }
                        setFormData(prev => ({ ...prev, chapters: newChapters }))
                      }}
                      placeholder="Titolo del capitolo"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Sintesi (opzionale)
                    </label>
                    <textarea
                      value={chapter.summary}
                      onChange={(e) => {
                        const newChapters = [...formData.chapters]
                        newChapters[index] = { ...newChapters[index], summary: e.target.value }
                        setFormData(prev => ({ ...prev, chapters: newChapters }))
                      }}
                      rows={2}
                      placeholder="Breve descrizione dei contenuti"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Minuti stimati (opzionale)
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={chapter.estimated_minutes}
                      onChange={(e) => {
                        const newChapters = [...formData.chapters]
                        newChapters[index] = { ...newChapters[index], estimated_minutes: e.target.value }
                        setFormData(prev => ({ ...prev, chapters: newChapters }))
                      }}
                      placeholder="45"
                      className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Tag
              </label>
              <button
                type="button"
                onClick={addTag}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                + Aggiungi tag
              </button>
            </div>
            {formData.tags.map((tag, index) => (
              <div key={index} className="flex items-center space-x-2 mb-2">
                <input
                  type="text"
                  value={tag}
                  onChange={(e) => {
                    const newTags = [...formData.tags]
                    newTags[index] = e.target.value
                    setFormData(prev => ({ ...prev, tags: newTags }))
                  }}
                  placeholder="Tag"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {formData.tags.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeTag(index)}
                    className="p-2 text-red-500 hover:text-red-700"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={loading || !formData.title.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creazione...' : 'Crea Libro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
