'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Brain, Download, RefreshCw, Loader2 } from 'lucide-react'

interface Book {
  id: string
  title: string
  author: string
  materials: Array<{
    filename: string
    file_path: string
  }>
}

export default function MindmapPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string
  const bookId = params.bookId as string

  const [book, setBook] = useState<Book | null>(null)
  const [courseName, setCourseName] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [mindmapContent, setMindmapContent] = useState<string>('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchBook()
    fetchCourseInfo()
  }, [courseId, bookId])

  const fetchBook = async () => {
    try {
      const response = await fetch(`/api/courses/${courseId}/books/${bookId}`)
      if (response.ok) {
        const data = await response.json()
        setBook(data.book)
      } else {
        setError('Errore nel caricamento del libro')
      }
    } catch (error) {
      setError('Errore nel caricamento del libro')
    } finally {
      setLoading(false)
    }
  }

  const fetchCourseInfo = async () => {
    try {
      const response = await fetch(`/api/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setCourseName(data.course.name)
      }
    } catch (error) {
      console.error('Error fetching course info:', error)
    }
  }

  const generateMindmap = async () => {
    if (!book || book.materials.length === 0) {
      setError('Nessun materiale disponibile per generare la mappa concettuale')
      return
    }

    setGenerating(true)
    setError('')

    try {
      // In a real implementation, this would call your backend API to generate a mindmap
      // For now, we'll create a simple text-based mindmap
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `Crea una mappa concettuale dettagliata del libro "${book.title}" di ${book.author}. Organizza i concetti principali in modo gerarchico, usando il formato:

# Libro: [Titolo]
## Capitolo 1: [Nome Capitolo]
### Concetto Principale
- Sottoconcetto 1
- Sottoconcetto 2
### Altro Concetto
- Dettaglio
- Esempio

Utilizza una struttura chiara e gerarchica che rappresenti bene il contenuto del libro.`,
          course_id: courseId,
          book_id: bookId
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setMindmapContent(data.response)
      } else {
        setError('Errore durante la generazione della mappa concettuale')
      }
    } catch (error) {
      setError('Errore durante la generazione della mappa concettuale')
    } finally {
      setGenerating(false)
    }
  }

  const downloadMindmap = () => {
    if (!mindmapContent) return

    const blob = new Blob([mindmapContent], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mindmap-${book?.title || 'book'}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento...</p>
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
              href={`/courses/${courseId}/books/${bookId}`}
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
                <Link href={`/courses/${courseId}/books/${bookId}`} className="hover:text-gray-700">
                  {book?.title}
                </Link>
                <span className="mx-2">/</span>
                <span className="text-gray-900">Mappa Concettuale</span>
              </nav>
              <h1 className="text-3xl font-bold text-gray-900">Mappa Concettuale</h1>
              <p className="text-gray-600 mt-1">{book?.title}</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Brain className="h-6 w-6 text-purple-600" />
                <h2 className="text-xl font-semibold text-gray-900">Mappa Concettuale del Libro</h2>
              </div>
              <div className="flex items-center space-x-3">
                {!mindmapContent && (
                  <button
                    onClick={generateMindmap}
                    disabled={generating || !book || book.materials.length === 0}
                    className="btn btn-primary flex items-center space-x-2"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Generazione...</span>
                      </>
                    ) : (
                      <>
                        <Brain className="h-4 w-4" />
                        <span>Genera Mappa</span>
                      </>
                    )}
                  </button>
                )}

                {mindmapContent && (
                  <>
                    <button
                      onClick={generateMindmap}
                      disabled={generating}
                      className="btn btn-secondary flex items-center space-x-2"
                    >
                      <RefreshCw className="h-4 w-4" />
                      <span>Regenera</span>
                    </button>
                    <button
                      onClick={downloadMindmap}
                      className="btn btn-secondary flex items-center space-x-2"
                    >
                      <Download className="h-4 w-4" />
                      <span>Scarica</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="p-6">
            {!mindmapContent ? (
              <div className="text-center py-12">
                <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {book?.materials && book.materials.length > 0
                    ? "Genera una mappa concettuale"
                    : "Nessun materiale disponibile"}
                </h3>
                <p className="text-gray-600 mb-6">
                  {book?.materials && book.materials.length > 0
                    ? "Analizza i contenuti del libro e crea una visualizzazione gerarchica dei concetti principali"
                    : "Carica dei materiali PDF per poter generare una mappa concettuale"}
                </p>
                {book?.materials && book.materials.length > 0 && (
                  <button
                    onClick={generateMindmap}
                    disabled={generating}
                    className="btn btn-primary"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generazione in corso...
                      </>
                    ) : (
                      <>
                        <Brain className="h-4 w-4 mr-2" />
                        Genera Mappa Concettuale
                      </>
                    )}
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-sm text-purple-700">
                    <strong>Nota:</strong> Questa è una mappa concettuale generata dall'IA basata sui materiali caricati.
                    Verifica sempre le informazioni importanti.
                  </p>
                </div>

                <div className="prose prose-purple max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
                    {mindmapContent}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}