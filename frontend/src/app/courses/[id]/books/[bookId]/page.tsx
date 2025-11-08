'use client'

import { useState, useEffect, type ChangeEvent } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, BookOpen, FileText, MessageSquare, Brain, Upload, Edit, Clock, Play } from 'lucide-react'
import SlideGenerator from '@/components/SlideGenerator'
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
  isbn: string
  description: string
  year: string
  publisher: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
  chapters: BookChapter[]
  tags: string[]
  materials: Array<{
    filename: string
    size: number
    uploaded_at: string
    file_path: string
  }>
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
    isbn: toStringValue(record.isbn),
    description: toStringValue(record.description),
    year: toStringValue(record.year),
    publisher: toStringValue(record.publisher),
    materials_count: toFiniteNumber(record.materials_count),
    study_sessions: toFiniteNumber(record.study_sessions),
    total_study_time: toFiniteNumber(record.total_study_time),
    created_at: toStringValue(record.created_at),
    chapters: normalizedChapters,
    tags: Array.isArray(record.tags) ? record.tags.map(tag => toStringValue(tag)).filter(Boolean) : [],
    materials: Array.isArray(record.materials) ? record.materials as Book['materials'] : []
  }
}

export default function BookPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string
  const bookId = params.bookId as string

  const [book, setBook] = useState<Book | null>(null)
  const [courseName, setCourseName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    fetchBook()
    fetchCourseInfo()
  }, [courseId, bookId])

  const fetchBook = async () => {
    try {
      const response = await fetchFromBackend(`/api/courses/${courseId}/books/${bookId}`)
      if (response.ok) {
        const data = await response.json()
        setBook(normalizeBook(data.book))
      } else {
        setError('Errore nel caricamento del libro')
      }
    } catch {
      setError('Errore nel caricamento del libro')
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

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    // Validate all files are PDFs
    for (let i = 0; i < files.length; i++) {
      if (!files[i].name.endsWith('.pdf')) {
        alert('Sono ammessi solo file PDF')
        return
      }
    }

    setUploading(true)
    let successCount = 0
    let errorCount = 0

    try {
      // Upload each file sequentially
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)

        try {
          const response = await fetchFromBackend(`/api/courses/${courseId}/books/${bookId}/upload`, {
            method: 'POST',
            body: formData,
          })

          if (response.ok) {
            successCount++
          } else {
            errorCount++
          }
        } catch {
          errorCount++
        }
      }

      // Refresh book data
      await fetchBook()

      // Show results
      if (successCount > 0 && errorCount === 0) {
        alert(`${successCount} materiale/i caricato con successo!`)
      } else if (successCount > 0 && errorCount > 0) {
        alert(`${successCount} materiale/i caricato con successo, ${errorCount} fallito/i`)
      } else {
        alert('Errore durante il caricamento dei materiali')
      }
    } catch {
      alert('Errore durante il caricamento dei materiali')
    } finally {
      setUploading(false)
      // Clear the file input
      event.target.value = ''
    }
  }

  const startStudySession = () => {
    router.push(`/chat?course=${courseId}&book=${bookId}`)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento libro...</p>
        </div>
      </div>
    )
  }

  if (!book) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Libro non trovato</h3>
          <p className="text-gray-600 mb-4">Il libro richiesto non è disponibile</p>
          <Link
            href={`/courses/${courseId}/books`}
            className="text-blue-600 hover:text-blue-700"
          >
            ← Torna ai libri
          </Link>
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
              href={`/courses/${courseId}/books`}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </Link>
            <div className="flex-1">
              <nav className="text-sm text-gray-500 mb-2">
                <Link href={`/courses/${courseId}`} className="hover:text-gray-700">
                  {courseName}
                </Link>
                <span className="mx-2">/</span>
                <Link href={`/courses/${courseId}/books`} className="hover:text-gray-700">
                  Libri
                </Link>
                <span className="mx-2">/</span>
                <span className="text-gray-900">{book.title}</span>
              </nav>
              <h1 className="text-3xl font-bold text-gray-900">{book.title}</h1>
              <p className="text-gray-600 mt-1">{book.author}</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Book Info */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Informazioni Libro</h2>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Autore</p>
                  <p className="font-medium text-gray-900">{book.author || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Anno</p>
                  <p className="font-medium text-gray-900">{book.year || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Editore</p>
                  <p className="font-medium text-gray-900">{book.publisher || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">ISBN</p>
                  <p className="font-medium text-gray-900">{book.isbn || 'N/A'}</p>
                </div>
              </div>

              {book.description && (
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">Descrizione</p>
                  <p className="text-gray-700">{book.description}</p>
                </div>
              )}

              {book.tags && book.tags.length > 0 && (
                <div>
                  <p className="text-sm text-gray-600 mb-2">Tag</p>
                  <div className="flex flex-wrap gap-2">
                    {book.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Chapters */}
            {book.chapters && book.chapters.length > 0 && (
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Capitoli</h2>
                <div className="space-y-2">
                  {book.chapters.map((chapter, index) => (
                    <div
                      key={index}
                      className="p-4 bg-gray-50 rounded-lg space-y-2"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-800">{chapter.title}</p>
                            {chapter.summary && (
                              <p className="text-sm text-gray-600 mt-1">
                                {chapter.summary}
                              </p>
                            )}
                          </div>
                        </div>
                        {typeof chapter.estimated_minutes === 'number' && (
                          <div className="flex items-center space-x-1 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            <span>{chapter.estimated_minutes} min</span>
                          </div>
                        )}
                      </div>
                      {!chapter.summary && !chapter.estimated_minutes && (
                        <p className="text-sm text-gray-500">
                          Nessuna descrizione aggiunta per questo capitolo.
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Materials */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Materiali</h2>
                <label className="btn btn-primary cursor-pointer">
                  <Upload className="h-4 w-4 mr-2" />
                  {uploading ? 'Caricamento...' : 'Carica PDF'}
                  <input
                    type="file"
                    accept=".pdf"
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
              </div>

              {book.materials && book.materials.length > 0 ? (
                <div className="space-y-3">
                  {book.materials.map((material, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="font-medium text-gray-900">{material.filename}</p>
                          <p className="text-sm text-gray-500">
                            {(material.size / 1024 / 1024).toFixed(2)} MB •
                            {new Date(material.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">Nessun materiale caricato</p>
                  <label className="btn btn-secondary cursor-pointer">
                    <Upload className="h-4 w-4 mr-2" />
                    Carica il primo materiale
                    <input
                      type="file"
                      accept=".pdf"
                      multiple
                      onChange={handleFileUpload}
                      className="hidden"
                      disabled={uploading}
                    />
                  </label>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Azioni Rapide</h2>
              <div className="space-y-3">
                <button
                  onClick={startStudySession}
                  className="w-full btn btn-primary group"
                >
                  <Play className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                  Inizia Sessione di Studio
                </button>

                <Link
                  href={`/chat?course=${courseId}&book=${bookId}`}
                  className="w-full btn btn-success group flex justify-center"
                >
                  <MessageSquare className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                  Chat con il Tutor
                </Link>

                <Link
                  href={`/courses/${courseId}/books/${bookId}/mindmap`}
                  className="w-full btn btn-secondary group flex justify-center"
                >
                  <Brain className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                  Mappa Concettuale
                </Link>

                <SlideGenerator
                  bookId={bookId}
                  courseId={courseId}
                  bookTitle={book.title}
                  bookAuthor={book.author}
                />

                <Link
                  href={`/courses/${courseId}/books/${bookId}/edit`}
                  className="w-full btn btn-secondary group flex justify-center"
                >
                  <Edit className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                  Modifica Libro
                </Link>
              </div>
            </div>

            {/* Stats */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistiche</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-600">Materiali</span>
                  </div>
                  <span className="font-medium text-gray-900">{book.materials_count}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-600">Sessioni</span>
                  </div>
                  <span className="font-medium text-gray-900">{book.study_sessions}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-600">Tempo Studio</span>
                  </div>
                  <span className="font-medium text-gray-900">
                    {Math.round(book.total_study_time / 60)}h
                  </span>
                </div>
              </div>
            </div>

            {/* Progress */}
            {book.study_sessions > 0 && (
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Progresso</h2>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Completamento</span>
                      <span className="font-medium text-gray-900">
                        {Math.min(100, (book.study_sessions / 10) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, (book.study_sessions / 10) * 100)}%`
                        }}
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">
                    {book.study_sessions} sessioni completate su 10 raccomandate
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
