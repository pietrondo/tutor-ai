'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Save, X, BookOpen, User, FileText } from 'lucide-react'

interface Course {
  id: string
  name: string
  description: string
  subject: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
}

export default function EditCoursePage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject: ''
  })

  useEffect(() => {
    fetchCourse()
  }, [courseId])

  const fetchCourse = async () => {
    try {
      const response = await fetch(`http://localhost:8000/courses/${courseId}`)
      const data = await response.json()

      if (response.ok) {
        setCourse(data.course)
        setFormData({
          name: data.course.name,
          description: data.course.description,
          subject: data.course.subject
        })
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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name.trim() || !formData.subject.trim()) {
      setError('Il nome e la materia sono obbligatori')
      return
    }

    setSaving(true)
    setError('')

    try {
      const response = await fetch(`http://localhost:8000/courses/${courseId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        router.push(`/courses/${courseId}`)
      } else {
        const data = await response.json()
        setError(data.detail || 'Errore nell\'aggiornamento del corso')
      }
    } catch (error) {
      console.error('Errore nell\'aggiornamento del corso:', error)
      setError('Errore di connessione al server')
    } finally {
      setSaving(false)
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
        <Link href="/courses" className="btn btn-primary">
          Torna ai Corsi
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Link
            href={`/courses/${courseId}`}
            className="inline-flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna al Corso
          </Link>

          <Link
            href={`/courses/${courseId}`}
            className="text-gray-600 hover:text-gray-900"
          >
            <X className="h-5 w-5" />
          </Link>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-lg">
              <BookOpen className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Modifica Corso</h1>
              <p className="text-gray-600">Aggiorna le informazioni del corso</p>
            </div>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Nome del Corso */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Nome del Corso *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <BookOpen className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
                className="pl-10 w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Es: Programmazione Python Base"
              />
            </div>
          </div>

          {/* Materia */}
          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
              Materia *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                id="subject"
                name="subject"
                value={formData.subject}
                onChange={handleInputChange}
                required
                className="pl-10 w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Es: Informatica, Matematica, Fisica"
              />
            </div>
          </div>

          {/* Descrizione */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Descrizione
            </label>
            <div className="relative">
              <div className="absolute top-3 left-3 pointer-events-none">
                <FileText className="h-5 w-5 text-gray-400" />
              </div>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="pl-10 w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
                placeholder="Descrizione dettagliata del corso, argomenti trattati, obiettivi, etc."
              />
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Statistiche Corso</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="text-xl font-bold text-blue-900">{course.materials_count}</div>
                  <div className="text-sm text-blue-700">Materiali caricati</div>
                </div>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <div className="h-5 w-5 bg-green-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">S</span>
                </div>
                <div>
                  <div className="text-xl font-bold text-green-900">{course.study_sessions}</div>
                  <div className="text-sm text-green-700">Sessioni di studio</div>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <div className="h-5 w-5 bg-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">T</span>
                </div>
                <div>
                  <div className="text-xl font-bold text-purple-900">
                    {Math.floor(course.total_study_time / 60)}h {course.total_study_time % 60}m
                  </div>
                  <div className="text-sm text-purple-700">Tempo di studio</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex justify-end space-x-4">
            <Link
              href={`/courses/${courseId}`}
              className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Annulla
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
            >
              {saving ? (
                <>
                  <div className="loading-spinner h-4 w-4"></div>
                  <span>Salvataggio...</span>
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  <span>Salva Modifiche</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}