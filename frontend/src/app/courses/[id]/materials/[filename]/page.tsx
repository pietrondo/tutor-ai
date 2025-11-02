'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, FileText, AlertCircle } from 'lucide-react'
import { PDFViewer } from '@/components/PDFViewer'
import Link from 'next/link'

interface MaterialInfo {
  filename: string
  size: number
  uploaded_at: string
  file_path: string
  course_name: string
}

export default function PDFViewerPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string
  const filename = params.filename as string

  const [materialInfo, setMaterialInfo] = useState<MaterialInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pdfUrl, setPdfUrl] = useState<string>('')

  useEffect(() => {
    fetchMaterialInfo()
  }, [courseId, filename])

  const fetchMaterialInfo = async () => {
    try {
      setLoading(true)
      // First get course info
      const courseResponse = await fetch(`http://localhost:8000/courses/${courseId}`)
      if (!courseResponse.ok) {
        throw new Error('Corso non trovato')
      }

      const courseData = await courseResponse.json()
      const course = courseData.course

      // Check if the material exists in course materials
      if (course.materials) {
        const material = course.materials.find((m: any) =>
          m.filename === filename || m.file_path.includes(filename)
        )

        if (!material) {
          throw new Error('Materiale non trovato')
        }

        setMaterialInfo({
          filename: material.filename,
          size: material.size,
          uploaded_at: material.uploaded_at,
          file_path: material.file_path,
          course_name: course.name
        })

        // Construct PDF URL
        const baseUrl = process.env.NODE_ENV === 'development'
          ? 'http://localhost:8000'
          : window.location.origin
        setPdfUrl(`${baseUrl}/uploads/${encodeURIComponent(filename)}`)
      } else {
        throw new Error('Nessun materiale trovato per questo corso')
      }
    } catch (error) {
      console.error('Error fetching material info:', error)
      setError(error instanceof Error ? error.message : 'Errore nel caricamento del materiale')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveAnnotations = (annotations: any[]) => {
    // Save annotations to backend or localStorage
    console.log('Saving annotations:', annotations)
    // TODO: Implement backend save
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Caricamento PDF...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="max-w-md w-full text-center p-6">
          <div className="flex justify-center mb-4">
            <AlertCircle className="h-12 w-12 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Errore</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            href={`/courses/${courseId}`}
            className="inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna al Corso
          </Link>
        </div>
      </div>
    )
  }

  if (!materialInfo || !pdfUrl) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Materiale non trovato</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* PDF Viewer */}
      <PDFViewer
        pdfUrl={pdfUrl}
        title={materialInfo.filename}
        onBack={() => router.push(`/courses/${courseId}`)}
        onSave={handleSaveAnnotations}
      />

      {/* Material Info Footer - Only shown when needed */}
      {false && ( // Set to true if you want to show this info
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span><strong>File:</strong> {materialInfo.filename}</span>
              <span><strong>Dimensione:</strong> {formatFileSize(materialInfo.size)}</span>
              <span><strong>Caricato:</strong> {formatDate(materialInfo.uploaded_at)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-gray-500">Corso:</span>
              <Link
                href={`/courses/${courseId}`}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                {materialInfo.course_name}
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}