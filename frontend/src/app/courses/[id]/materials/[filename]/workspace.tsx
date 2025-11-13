'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import {
  BookOpen,
  MessageCircle,
  FileText,
  Settings,
  ArrowLeft,
  Download,
  Maximize2,
  Menu,
  X,
  Brain,
  Eye
} from 'lucide-react'

// Dynamic imports to avoid SSR issues with PDF.js
const EnhancedPDFReader = dynamic(() => import('@/components/EnhancedPDFReader'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-4 text-gray-600">Caricamento lettore PDF...</p>
      </div>
    </div>
  )
})

const ChatWrapper = dynamic(() => import('@/components/ChatWrapper'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Caricamento chat...</p>
      </div>
    </div>
  )
})

const MindmapExplorer = dynamic(() => import('@/components/MindmapExplorer').then(mod => ({ default: mod.MindmapExplorer })), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Caricamento mindmap...</p>
      </div>
    </div>
  )
})

interface StudyMaterial {
  filename: string
  file_path: string
  size?: number
  pdf_url?: string
}

interface StudyBook {
  id: string
  title: string
  materials?: StudyMaterial[]
}

export default function MaterialWorkspace() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const courseId = params.id as string
  const filename = params.filename as string

  // States
  const [book, setBook] = useState<StudyBook | null>(null)
  const [bookId, setBookId] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string>('')
  const [layoutMode, setLayoutMode] = useState<'split' | 'pdf-focus' | 'chat-focus'>('split')
  const [rightPanelTab, setRightPanelTab] = useState<'chat' | 'mindmap'>('chat')
  const [mindmapScope, setMindmapScope] = useState<'book' | 'pdf'>('book')
  const [mindmap, setMindmap] = useState<any>(null)

  // Find book ID by searching through all books in the course to find which one contains the material
  const getBookIdFromParams = useCallback(async (filename: string, courseId: string): Promise<string> => {
    try {
      // First try to get bookId from query string (most reliable)
      const queryBookId = new URLSearchParams(window.location.search).get('book')
      if (queryBookId) {
        return queryBookId
      }

      // Decode the filename from URL encoding
      const decodedFilename = decodeURIComponent(filename)
      console.log('Material lookup:', {
        original: filename,
        decoded: decodedFilename
      })

      // If no query param, search through all books in the course to find the material
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const courseResponse = await fetch(`${API_BASE_URL}/courses/${courseId}`)
      if (!courseResponse.ok) {
        throw new Error('Corso non trovato')
      }

      const courseData = await courseResponse.json()
      const books = courseData.course?.books || []

      // Search through each book's materials to find the matching filename
      for (const book of books) {
        const materials = book.materials || []
        const material = materials.find(
          (m: StudyMaterial) => m.filename === decodedFilename ||
                              m.filename === filename || // fallback to encoded version
                              m.file_path?.includes(decodedFilename) ||
                              m.file_path?.includes(filename)
        )
        if (material) {
          console.log('Found material in book:', {
            bookId: book.id,
            material: material.filename,
            matched: material.filename === decodedFilename ? 'decoded' : 'encoded'
          })
          return book.id
        }
      }

      throw new Error(`Material not found in any book: ${decodedFilename} (original: ${filename})`)
    } catch (error) {
      console.error('Error finding book ID:', error)
      throw error
    }
  }, [])

  useEffect(() => {
    loadBookAndMaterial()
  }, [courseId, filename, searchParams])

  const loadBookAndMaterial = async () => {
    try {
      setIsLoading(true)

      // Find the book ID that contains this material
      const resolvedBookId = await getBookIdFromParams(filename, courseId)
      setBookId(resolvedBookId)

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const courseResponse = await fetch(`${API_BASE_URL}/courses/${courseId}`)
      if (!courseResponse.ok) {
        throw new Error('Corso non trovato')
      }

      const courseData = await courseResponse.json()
      const books = courseData.course?.books || []
      const foundBook = books.find((b: StudyBook) => b.id === resolvedBookId)

      if (!foundBook) {
        throw new Error(`Libro non trovato. BookId: ${resolvedBookId}, Available books: ${books.length}`)
      }

      setBook(foundBook)

      // Find the specific material (try both decoded and encoded filenames)
      const decodedFilename = decodeURIComponent(filename)
      const materials = foundBook.materials || []
      const material = materials.find(
        (m: StudyMaterial) => m.filename === decodedFilename ||
                            m.filename === filename || // fallback to encoded version
                            m.file_path?.includes(decodedFilename) ||
                            m.file_path?.includes(filename)
      )

      if (material) {
        // Construct PDF URL using relative path for Next.js rewrite (use the original filename for URL encoding)
        const pdfFilename = material.filename // Use the actual filename from the material
        const directPdfUrl = `/course-files/${courseId}/books/${resolvedBookId}/${encodeURIComponent(pdfFilename)}`
        console.log('PDF URL construction:', {
          materialFilename: pdfFilename,
          urlFilename: encodeURIComponent(pdfFilename),
          finalUrl: directPdfUrl
        })
        setPdfUrl(directPdfUrl)
      } else {
        console.error('Available materials:', materials.map(m => m.filename))
        throw new Error(`Materiale non trovato. Filename: ${decodedFilename} (original: ${filename}), Available materials: ${materials.length}`)
      }

      setError(null)
    } catch (err) {
      console.error('Error loading material:', err)
      setError(err instanceof Error ? err.message : 'Errore nel caricamento del materiale')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank')
    }
  }

  const loadMindmap = async () => {
    try {
      const bookId = await getBookIdFromParams(filename, courseId)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/mindmap/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: courseId,
          book_id: bookId,
          scope: mindmapScope,
          pdf_filename: mindmapScope === 'pdf' ? filename : undefined
        })
      })

      if (response.ok) {
        const data = await response.json()
        setMindmap(data)
      }
    } catch (error) {
      console.error('Errore caricamento mindmap:', error)
    }
  }

  // Load mindmap when switching to mindmap tab
  useEffect(() => {
    if (rightPanelTab === 'mindmap') {
      loadMindmap()
    }
  }, [rightPanelTab, mindmapScope])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento workspace...</p>
          <p className="text-sm text-gray-500 mt-2">PDF + Chat + Annotazioni</p>
        </div>
      </div>
    )
  }

  if (error || !book) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full text-center p-6">
          <div className="flex justify-center mb-4">
            <FileText className="h-12 w-12 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Errore</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.back()}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{book.title}</h1>
              <p className="text-sm text-gray-500">{filename}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownload}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Download PDF"
            >
              <Download className="h-4 w-4 text-gray-600" />
            </button>

            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setLayoutMode('pdf-focus')}
                className={`p-2 rounded transition-colors ${
                  layoutMode === 'pdf-focus' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                }`}
                title="Focus PDF"
              >
                <BookOpen className="h-4 w-4 text-gray-600" />
              </button>
              <button
                onClick={() => setLayoutMode('split')}
                className={`p-2 rounded transition-colors ${
                  layoutMode === 'split' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                }`}
                title="Split View"
              >
                <Menu className="h-4 w-4 text-gray-600" />
              </button>
              <button
                onClick={() => setLayoutMode('chat-focus')}
                className={`p-2 rounded transition-colors ${
                  layoutMode === 'chat-focus' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                }`}
                title="Focus Chat"
              >
                <MessageCircle className="h-4 w-4 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* PDF Panel */}
        <div className={`${layoutMode === 'chat-focus' ? 'hidden md:hidden' : ''} ${
          layoutMode === 'pdf-focus' ? 'flex-1' : layoutMode === 'split' ? 'w-1/2' : 'w-1/2'
        } bg-white border-r border-gray-200 overflow-auto cv-auto`}>
          {pdfUrl && bookId && (
            <EnhancedPDFReader
              pdfUrl={pdfUrl}
              pdfFilename={filename}
              bookId={bookId}
              courseId={courseId}
              userId="default-user"
              onAnnotationCreate={(annotation) => {
                console.log('Annotation created:', annotation);
              }}
              onAnnotationUpdate={(annotation) => {
                console.log('Annotation updated:', annotation);
              }}
              onChatWithContext={(context) => {
                console.log('Chat context:', context);
              }}
            />
          )}
        </div>

        {/* Right Panel with Tabs */}
        <div className={`${layoutMode === 'pdf-focus' ? 'hidden md:hidden' : ''} ${
          layoutMode === 'chat-focus' ? 'flex-1' : layoutMode === 'split' ? 'w-1/2' : 'w-1/2'
        } bg-gray-50 flex flex-col`}>
          {/* Tab Navigation */}
          <div className="bg-white border-b border-gray-200">
            <div className="flex">
              <button
                onClick={() => setRightPanelTab('chat')}
                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 text-sm font-medium ${
                  rightPanelTab === 'chat'
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat Tutor</span>
              </button>
              <button
                onClick={() => setRightPanelTab('mindmap')}
                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 text-sm font-medium ${
                  rightPanelTab === 'mindmap'
                    ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>Mappa Concettuale</span>
              </button>
            </div>
            {rightPanelTab === 'mindmap' && (
              <div className="px-4 py-2 border-t border-gray-200 flex items-center gap-2 text-xs text-gray-600">
                <span>Scope:</span>
                <button
                  onClick={() => setMindmapScope('book')}
                  className={`px-2 py-1 rounded ${mindmapScope === 'book' ? 'bg-purple-100 text-purple-700' : 'hover:bg-gray-100'}`}
                  title="Mappa aggregata del libro"
                >
                  Libro
                </button>
                <button
                  onClick={() => setMindmapScope('pdf')}
                  className={`px-2 py-1 rounded ${mindmapScope === 'pdf' ? 'bg-purple-100 text-purple-700' : 'hover:bg-gray-100'}`}
                  title="Mappa del PDF corrente"
                >
                  PDF
                </button>
              </div>
            )}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto cv-auto">
            {rightPanelTab === 'chat' ? (
              <ChatWrapper course={courseId} book={bookId} />
            ) : (
              <div className="h-full p-4 overflow-auto">
                {mindmap ? (
                  <MindmapExplorer mindmap={mindmap} />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
                      <p className="mt-2 text-gray-600">Generazione mindmap in corso...</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer with PDF Navigation */}
      <footer className="bg-white border-t border-gray-200">
        {/* Other PDFs in this book */}
        {book.materials && book.materials.length > 1 && (
          <div className="border-b border-gray-200 px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Altri PDF in questo libro:</span>
              <Link
                href={`/courses/${courseId}/books/${bookId}`}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Vedi tutti →
              </Link>
            </div>
            <div className="flex flex-wrap gap-2">
              {book.materials
                .filter((material: StudyMaterial) => material.filename !== filename)
                .slice(0, 6) // Show max 6 other PDFs
                .map((material: StudyMaterial, index: number) => (
                  <Link
                    key={index}
                    href={`/courses/${courseId}/materials/${encodeURIComponent(material.filename)}?book=${bookId}`}
                    className="inline-flex items-center px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-xs text-gray-700 transition-colors"
                    title={`Apri ${material.filename}`}
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    {material.filename.length > 15
                      ? material.filename.substring(0, 12) + '...'
                      : material.filename
                    }
                  </Link>
                ))}
              {book.materials.filter((m: StudyMaterial) => m.filename !== filename).length > 6 && (
                <span className="text-xs text-gray-500 px-2 py-1">
                  +{book.materials.filter((m: StudyMaterial) => m.filename !== filename).length - 6} altri
                </span>
              )}
            </div>
          </div>
        )}

        <div className="px-4 py-2">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span>Layout: {layoutMode}</span>
              <span>•</span>
              <span>PDF + {rightPanelTab === 'chat' ? 'Chat' : 'Mindmap'}</span>
              {book.materials && (
                <>
                  <span>•</span>
                  <span>{book.materials.findIndex((m: StudyMaterial) => m.filename === filename) + 1} di {book.materials.length}</span>
                </>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                Workspace Attivo
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
