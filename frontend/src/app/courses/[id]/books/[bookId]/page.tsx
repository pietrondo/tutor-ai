'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, FileText, Download, Brain, BookOpen, Eye, Merge, RefreshCw } from 'lucide-react'
import EnhancedPDFReader from '@/components/EnhancedPDFReader'

interface BookInfo {
  id: string
  title: string
  author: string
  materials: Array<{
    filename: string
    size: number
  }>
}

interface PDFViewerState {
  showPDF: boolean
  selectedPDF: {
    filename: string
    url: string
  } | null
  pdfError: string | null
}

export default function SimpleBookPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string
  const bookId = params.bookId as string

  const [book, setBook] = useState<BookInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfState, setPdfState] = useState<PDFViewerState>({
    showPDF: false,
    selectedPDF: null,
    pdfError: null
  })
  const [isMerging, setIsMerging] = useState(false)
  const [mergeResult, setMergeResult] = useState<any>(null)

  useEffect(() => {
    fetchBook()
  }, [courseId, bookId])

  // Auto-open first PDF when book is loaded
  useEffect(() => {
    if (book && book.materials.length > 0 && !pdfState.showPDF) {
      // Find the first PDF file
      const firstPDF = book.materials.find(material =>
        material.filename.toLowerCase().endsWith('.pdf')
      )
      if (firstPDF) {
        handleOpenPDF(firstPDF)
      }
    }
  }, [book, pdfState.showPDF])

  const fetchBook = async () => {
    try {
      // Fetch the course data which contains all books/materials
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        const courseData = data.course
        const materials = courseData.materials || []

        // Group materials by book_id
        const booksMap = new Map()
        materials.forEach((material: any) => {
          const materialBookId = material.book_id
          if (materialBookId && !booksMap.has(materialBookId)) {
            booksMap.set(materialBookId, {
              id: materialBookId,
              title: `Book ${materialBookId.slice(0, 8)}...`,
              author: 'Unknown',
              materials: []
            })
          }
          if (materialBookId && booksMap.has(materialBookId)) {
            booksMap.get(materialBookId)?.materials.push({
              filename: material.filename,
              size: material.size
            })
          }
        })

        const foundBook = booksMap.get(bookId)
        if (foundBook) {
          setBook(foundBook)
          setError('')
        } else {
          setError(`Book not found. BookId: ${bookId}, Available books: ${Array.from(booksMap.keys()).join(', ')}`)
        }
      } else {
        setError('Errore nel caricamento del corso')
      }
    } catch (err) {
      console.error('Error fetching book:', err)
      setError('Errore nel caricamento del libro')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenPDF = (material: { filename: string; size: number }) => {
    const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/course-files/${courseId}/books/${bookId}/${encodeURIComponent(material.filename)}`

    setPdfState({
      showPDF: true,
      selectedPDF: {
        filename: material.filename,
        url: pdfUrl
      },
      pdfError: null
    })
  }

  const handleMergePDFs = async () => {
    if (!book || book.materials.length <= 1) {
      setError('Il libro deve contenere almeno 2 PDF per essere uniti')
      return
    }

    setIsMerging(true)
    setError('')
    setMergeResult(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/courses/${courseId}/books/${bookId}/merge-pdf`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore durante unione PDF')
      }

      const result = await response.json()
      setMergeResult(result)

      // Refresh book data to show the new merged PDF
      await fetchBook()

    } catch (error: any) {
      setError(`Errore: ${error.message}`)
    } finally {
      setIsMerging(false)
    }
  }

  const handleClosePDF = () => {
    setPdfState({
      showPDF: false,
      selectedPDF: null,
      pdfError: null
    })
  }

  const handlePDFError = (error: string | null) => {
    setPdfState(prev => ({
      ...prev,
      pdfError: error,
      showPDF: error ? false : prev.showPDF
    }))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-rose-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento libro...</p>
        </div>
      </div>
    )
  }

  if (error || !book) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-rose-50 flex items-center justify-center">
        <div className="text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">{error}</p>
          <Link
            href={`/courses/${courseId}`}
            className="inline-flex items-center px-4 py-2 mt-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-rose-50">
      <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/courses/${courseId}`}
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna al corso
          </Link>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{book.title}</h1>
            {book.author && <p className="text-gray-600">Autore: {book.author}</p>}
          </div>

          {/* Merge PDF Action */}
          {book.materials.length >= 1 && (
            <div className="flex justify-end">
              <button
                onClick={handleMergePDFs}
                disabled={isMerging}
                className="inline-flex items-center px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isMerging ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Unione in corso...
                  </>
                ) : (
                  <>
                    <Merge className="h-4 w-4 mr-2" />
                    Unisci tutti i PDF ({book.materials.length} file)
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Merge Success Display */}
        {mergeResult && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-800">✅ PDF Unito con Successo</h3>
                <p className="text-green-700 mb-2">
                  {mergeResult.merged_pdf?.total_files} PDF uniti in: {mergeResult.merged_pdf?.filename}
                </p>
                <p className="text-sm text-green-600">
                  Dimensione: {((mergeResult.merged_pdf?.size || 0) / (1024 * 1024)).toFixed(2)} MB
                </p>
                <details className="mt-2">
                  <summary className="text-sm text-green-600 cursor-pointer">File uniti</summary>
                  <ul className="text-xs text-green-600 mt-1 ml-4">
                    {mergeResult.merged_pdf?.files_merged?.map((filename: string, index: number) => (
                      <li key={index}>• {filename}</li>
                    ))}
                  </ul>
                </details>
              </div>
              <button
                onClick={() => setMergeResult(null)}
                className="text-green-500 hover:text-green-700"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* PDF Error Display */}
        {pdfState.pdfError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-red-800">Errore PDF</h3>
                <p className="text-red-700">{pdfState.pdfError}</p>
              </div>
              <button
                onClick={() => setPdfState(prev => ({ ...prev, pdfError: null }))}
                className="text-red-500 hover:text-red-700"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* PDF Viewer Section */}
        {pdfState.showPDF && pdfState.selectedPDF && (
          <div className="bg-white rounded-xl shadow-lg mb-8">
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center">
                <FileText className="h-6 w-6 text-blue-600 mr-2" />
                <h2 className="text-xl font-semibold text-gray-900">
                  {pdfState.selectedPDF.filename}
                </h2>
                {pdfLoading && (
                  <div className="ml-3">
                    <div className="w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                  </div>
                )}
              </div>
              <button
                onClick={handleClosePDF}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Chiudi PDF"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </button>
            </div>
            <div className="h-[800px] relative">
              {pdfLoading && (
                <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
                  <div className="text-center">
                    <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">Caricamento PDF...</p>
                  </div>
                </div>
              )}
              <EnhancedPDFReader
                pdfUrl={pdfState.selectedPDF.url}
                pdfFilename={pdfState.selectedPDF.filename}
                bookId={bookId}
                courseId={courseId}
                userId="default-user"
                onError={handlePDFError}
                onLoadingChange={setPdfLoading}
              />
            </div>
          </div>
        )}

        {/* Materials Section */}
        {book.materials && book.materials.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Materiali del Corso</h2>
            <div className="space-y-4">
              {book.materials.map((material, index) => {
                const directPdfUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/course-files/${courseId}/books/${bookId}/${encodeURIComponent(material.filename)}`
                const isPDF = material.filename.toLowerCase().endsWith('.pdf')
                const isActive = pdfState.selectedPDF?.filename === material.filename
                return (
                  <div key={index} className={`border rounded-lg p-4 ${isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <FileText className="h-8 w-8 text-blue-600 mr-3" />
                        <div>
                          <div className="flex items-center">
                            <h3 className="font-medium text-gray-900">{material.filename}</h3>
                            {isActive && (
                              <span className="ml-2 px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
                                Attivo
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">
                            Dimensione: {(material.size / (1024 * 1024)).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        {isPDF && (
                          <Link
                            href={`/courses/${courseId}/materials/${encodeURIComponent(material.filename)}?book=${bookId}`}
                            className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                            title="Read PDF in full workspace"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Read PDF
                          </Link>
                        )}
                        <a
                          href={`/courses/${courseId}/materials/${encodeURIComponent(material.filename)}`}
                          className="inline-flex items-center px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                        >
                          <BookOpen className="h-4 w-4 mr-1" />
                          Study Workspace
                        </a>
                        <a
                          href={directPdfUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-2 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700"
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </a>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link
            href={`/courses/${courseId}/books/${bookId}/mindmap`}
            className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow group"
          >
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-purple-600 mr-3 group-hover:scale-110 transition-transform" />
              <div>
                <h3 className="font-semibold text-gray-900">Mappa Concettuale</h3>
                <p className="text-sm text-gray-600">Genera una mindmap dei contenuti</p>
              </div>
            </div>
          </Link>

          <Link
            href={`/courses/${courseId}/study?book=${bookId}`}
            className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow group"
          >
            <div className="flex items-center">
              <BookOpen className="h-8 w-8 text-green-600 mr-3 group-hover:scale-110 transition-transform" />
              <div>
                <h3 className="font-semibold text-gray-900">Modalità Studio</h3>
                <p className="text-sm text-gray-600">Apri il libro in modalità studio</p>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}
