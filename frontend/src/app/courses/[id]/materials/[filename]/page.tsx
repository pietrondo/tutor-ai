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

type CourseMaterial = {
  filename: string
  file_path: string
  size?: number
  uploaded_at?: string
}

type CourseResponse = {
  course?: {
    name: string
    materials?: CourseMaterial[]
  }
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
      const courseResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses/${courseId}`)
      if (!courseResponse.ok) {
        throw new Error('Corso non trovato')
      }

      const coursePayload: CourseResponse = await courseResponse.json()
      const course = coursePayload.course

      if (!course) {
        throw new Error('Corso non trovato')
      }

      const materials: CourseMaterial[] = Array.isArray(course.materials) ? course.materials : []
      const material = materials.find(
        (item) =>
          typeof item.filename === 'string' &&
          typeof item.file_path === 'string' &&
          (item.filename === filename || item.file_path.includes(filename))
      )

      if (!material) {
        throw new Error('Materiale non trovato')
      }

      setMaterialInfo({
        filename: material.filename,
        size: material.size ?? 0,
        uploaded_at: material.uploaded_at ?? new Date().toISOString(),
        file_path: material.file_path,
        course_name: course.name
      })

      const baseUrl = process.env.NODE_ENV === 'development'
        ? process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
        : window.location.origin
      setPdfUrl(`${baseUrl}/uploads/${encodeURIComponent(filename)}`)
    } catch (error) {
      console.error('Error fetching material info:', error)
      setError(error instanceof Error ? error.message : 'Errore nel caricamento del materiale')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveAnnotations = (annotations: unknown[]) => {
    // Save annotations to backend or localStorage
    console.log('Saving annotations:', annotations)
    // TODO: Implement backend save
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

    </div>
  )
}
