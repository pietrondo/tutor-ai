'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Upload, FileText, MessageSquare, BarChart3, Trash2, Download } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { CourseMaterials } from '@/components/CourseMaterials'
import { StudyProgress } from '@/components/StudyProgress'

interface Course {
  id: string
  name: string
  description: string
  subject: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
  materials?: Array<{
    filename: string
    size: number
    uploaded_at: string
    file_path: string
  }>
}

export default function CourseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'materials' | 'progress' | 'quiz'>('materials')

  useEffect(() => {
    fetchCourse()
  }, [courseId])

  const fetchCourse = async () => {
    try {
      const response = await fetch(`http://localhost:8000/courses/${courseId}`)
      const data = await response.json()

      if (response.ok) {
        setCourse(data.course)
      } else {
        if (response.status === 404) {
          setError('Corso non trovato')
        } else {
          setError('Errore nel caricamento del corso')
        }
      }
    } catch (error) {
      console.error('Errore nel caricamento del corso:', error)
      setError('Errore di connessione al server')
    } finally {
      setLoading(false)
    }
  }

  const onDrop = async (acceptedFiles: File[]) => {
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf')

    if (pdfFiles.length === 0) {
      setError('Solo i file PDF sono ammessi')
      return
    }

    if (pdfFiles.length !== acceptedFiles.length) {
      setError('Alcuni file non sono PDF e sono stati ignorati')
    }

    setUploading(true)
    setError('')

    for (const file of pdfFiles) {
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch(`http://localhost:8000/courses/${courseId}/upload`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || `Errore nell'upload di ${file.name}`)
        }
      } catch (error) {
        console.error(`Errore nell'upload di ${file.name}:`, error)
        setError(`Errore nell'upload di ${file.name}`)
      }
    }

    setUploading(false)
    fetchCourse() // Refresh course data
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    disabled: uploading
  })

  const handleDeleteCourse = async () => {
    if (!confirm(`Sei sicuro di voler eliminare il corso "${course?.name}"? Questa azione non può essere annullata.`)) {
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/courses/${courseId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        router.push('/')
      } else {
        alert('Errore nell\'eliminazione del corso')
      }
    } catch (error) {
      console.error('Errore nell\'eliminazione del corso:', error)
      alert('Errore nell\'eliminazione del corso')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {error || 'Corso non trovato'}
        </h2>
        <Link href="/" className="btn btn-primary">
          Torna alla Home
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Link
            href="/"
            className="inline-flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna alla Home
          </Link>

          <button
            onClick={handleDeleteCourse}
            className="text-red-600 hover:text-red-800 flex items-center space-x-2"
          >
            <Trash2 className="h-4 w-4" />
            <span>Elimina Corso</span>
          </button>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{course.name}</h1>
              <p className="text-lg text-gray-600 mb-4">{course.subject}</p>
              <p className="text-gray-700 mb-6">{course.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <FileText className="h-6 w-6 text-blue-600 mb-2" />
                  <div className="text-2xl font-bold text-blue-900">{course.materials_count}</div>
                  <div className="text-sm text-blue-700">Materiali caricati</div>
                </div>

                <div className="bg-green-50 rounded-lg p-4">
                  <MessageSquare className="h-6 w-6 text-green-600 mb-2" />
                  <div className="text-2xl font-bold text-green-900">{course.study_sessions}</div>
                  <div className="text-sm text-green-700">Sessioni di studio</div>
                </div>

                <div className="bg-purple-50 rounded-lg p-4">
                  <BarChart3 className="h-6 w-6 text-purple-600 mb-2" />
                  <div className="text-2xl font-bold text-purple-900">
                    {Math.floor(course.total_study_time / 60)}h {course.total_study_time % 60}m
                  </div>
                  <div className="text-sm text-purple-700">Tempo totale di studio</div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 mt-6 pt-6 border-t border-gray-200">
            <Link
              href={`/chat?course=${course.id}`}
              className="btn btn-primary flex items-center space-x-2"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat con Tutor</span>
            </Link>

            <Link
              href={`/courses/${course.id}/quiz`}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <BarChart3 className="h-4 w-4" />
              <span>Crea Quiz</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('materials')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'materials'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Materiali del Corso
            </button>

            <button
              onClick={() => setActiveTab('progress')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'progress'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Progressi di Studio
            </button>

            <button
              onClick={() => setActiveTab('quiz')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'quiz'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Quiz e Test
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'materials' && (
            <div className="space-y-6">
              {/* Upload Area */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Carica Nuovi Materiali</h3>
                <div
                  {...getRootProps()}
                  className={`upload-area ${isDragActive ? 'dragover' : ''} ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <input {...getInputProps()} />
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  {uploading ? (
                    <div className="text-center">
                      <div className="loading-spinner mx-auto mb-2"></div>
                      <p className="text-gray-600">Caricamento in corso...</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-gray-600 mb-2">
                        {isDragActive
                          ? 'Rilascia i file qui...'
                          : 'Trascina i file PDF qui o clicca per selezionare'
                        }
                      </p>
                      <p className="text-sm text-gray-500">
                        Solo file PDF sono supportati
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              {/* Materials List */}
              <CourseMaterials
                materials={course.materials || []}
                onRefresh={fetchCourse}
                courseId={courseId}
              />
            </div>
          )}

          {activeTab === 'progress' && (
            <StudyProgress courseId={courseId} />
          )}

          {activeTab === 'quiz' && (
            <div className="text-center py-8">
              <Link
                href={`/courses/${course.id}/quiz`}
                className="btn btn-primary"
              >
                Crea un Nuovo Quiz
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}