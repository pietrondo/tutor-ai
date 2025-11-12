'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, BookOpen, FileText, MessageSquare, Edit, Clock, Play, Eye } from 'lucide-react'

const StudyIcon = BookOpen

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
  chapters: any[]
  tags: string[]
  materials: Array<{
    filename: string
    size: number
    uploaded_at: string
    file_path: string
  }>
}

export default function WorkingBookPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()

  const bookId = params.bookId as string
  const courseId = searchParams.get('course') as string

  const [book, setBook] = useState<Book | null>(null)
  const [courseName, setCourseName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (courseId && bookId) {
      fetchBook()
      fetchCourseInfo()
    }
  }, [courseId, bookId])

  const fetchBook = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/books/${bookId}`)
      if (response.ok) {
        const data = await response.json()
        setBook(data.book)
      } else {
        setError('Errore nel caricamento del libro')
      }
    } catch (err) {
      setError('Errore nel caricamento del libro')
    } finally {
      setLoading(false)
    }
  }

  const fetchCourseInfo = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setCourseName(data.course.name)
      }
    } catch (err) {
      console.error('Error fetching course info:', err)
    }
  }

  const startStudySession = () => {
    router.push(`/chat?course=${courseId}&book=${bookId}`)
  }

  if (!courseId || !bookId) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">URL non valido</h3>
          <p className="text-gray-600">Formato URL richiesto: /book/bookId?course=courseId</p>
          <Link href="/courses" className="text-blue-600 hover:text-blue-700 mt-4 inline-block">
            ← Torna ai corsi
          </Link>
        </div>
      </div>
    )
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
          <Link href={`/courses/${courseId}/books`} className="text-blue-600 hover:text-blue-700">
            ← Torna ai libri
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

            {/* Materials */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Materiali</h2>
              </div>

              {book.materials && book.materials.length > 0 ? (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Materiali Disponibili</h3>
                  {book.materials.map((material, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3 flex-1">
                          <FileText className="h-6 w-6 text-blue-500 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">{material.filename}</p>
                            <p className="text-sm text-gray-500">
                              {(material.size / 1024 / 1024).toFixed(2)} MB •
                              {new Date(material.uploaded_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Link
                          href={`/courses/${courseId}/materials/${encodeURIComponent(material.filename)}`}
                          className="inline-flex items-center px-3 py-2 bg-blue-100 text-blue-700 text-sm rounded-md hover:bg-blue-200 transition-colors"
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          Leggi PDF
                        </Link>

                        <Link
                          href={`/courses/${courseId}/study?book=${bookId}&pdf=${encodeURIComponent(material.filename)}`}
                          className="inline-flex items-center px-3 py-2 bg-green-100 text-green-700 text-sm rounded-md hover:bg-green-200 transition-colors"
                        >
                          <StudyIcon className="h-4 w-4 mr-1" />
                          Studio Integrato
                        </Link>

                        <Link
                          href={`/chat?course=${courseId}&book=${bookId}&pdf=${encodeURIComponent(material.filename)}`}
                          className="inline-flex items-center px-3 py-2 bg-purple-100 text-purple-700 text-sm rounded-md hover:bg-purple-200 transition-colors"
                        >
                          <MessageSquare className="h-4 w-4 mr-1" />
                          Chat con Tutor
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">Nessun materiale caricato</p>
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
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors group"
                >
                  <Play className="inline h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                  Inizia Sessione di Studio
                </button>

                <Link href={`/chat?course=${courseId}&book=${bookId}`}>
                  <button className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors group">
                    <MessageSquare className="inline h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                    Chat con il Tutor
                  </button>
                </Link>

                <Link href={`/courses/${courseId}/books/${bookId}/edit`}>
                  <button className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors group">
                    <Edit className="inline h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                    Modifica Libro
                  </button>
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
          </div>
        </div>
      </div>
    </div>
  )
}
