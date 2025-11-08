'use client'

import { useState, useEffect, type ChangeEvent, type FormEvent } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Plus, Brain, FileText, Clock, Trash2, Edit } from 'lucide-react'

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

interface Quiz {
  id: string
  title: string
  description: string
  question_count: number
  difficulty: 'facile' | 'medio' | 'difficile'
  created_at: string
  is_active: boolean
}

export default function QuizPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingQuiz, setEditingQuiz] = useState<Quiz | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    difficulty: 'medio' as 'facile' | 'medio' | 'difficile'
  })

  useEffect(() => {
    fetchCourse()
    fetchQuizzes()
  }, [courseId])

  const fetchCourse = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses/${courseId}`)
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
    }
  }

  const fetchQuizzes = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses/${courseId}/quizzes`)
      const data = await response.json()

      if (response.ok) {
        setQuizzes(data.quizzes || [])
      }
    } catch (error) {
      console.error('Errore nel caricamento dei quiz:', error)
    }
  }

  const handleInputChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = event.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()

    if (!formData.title.trim()) {
      setError('Il titolo è obbligatorio')
      return
    }

    setLoading(true)
    setError('')

    try {
      const url = editingQuiz
        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses/${courseId}/quizzes/${editingQuiz.id}`
        : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses/${courseId}/quizzes`

      const response = await fetch(url, {
        method: editingQuiz ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setShowCreateForm(false)
        setEditingQuiz(null)
        setFormData({ title: '', description: '', difficulty: 'medio' })
        fetchQuizzes()
      } else {
        const data = await response.json()
        setError(data.detail || 'Errore nel salvataggio del quiz')
      }
    } catch (error) {
      console.error('Errore nel salvataggio del quiz:', error)
      setError('Errore di connessione al server')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (quiz: Quiz) => {
    setEditingQuiz(quiz)
    setFormData({
      title: quiz.title,
      description: quiz.description,
      difficulty: quiz.difficulty
    })
    setShowCreateForm(true)
  }

  const handleDelete = async (quizId: string) => {
    if (!confirm('Sei sicuro di voler eliminare questo quiz?')) {
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses/${courseId}/quizzes/${quizId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchQuizzes()
      } else {
        alert('Errore nell\'eliminazione del quiz')
      }
    } catch (error) {
      console.error('Errore nell\'eliminazione del quiz:', error)
      alert('Errore nell\'eliminazione del quiz')
    }
  }

  const handleCreateQuestions = (quizId: string) => {
    router.push(`/courses/${courseId}/quiz/${quizId}/questions`)
  }

  if (loading && !course) {
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
    <div className="max-w-6xl mx-auto">
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

          <button
            onClick={() => {
              setShowCreateForm(true)
              setEditingQuiz(null)
              setFormData({ title: '', description: '', difficulty: 'medio' })
            }}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Crea Nuovo Quiz</span>
          </button>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Quiz del Corso</h1>
              <p className="text-gray-600">{course.name}</p>
            </div>
          </div>

          <div className="text-sm text-gray-500">
            {quizzes.length} {quizzes.length === 1 ? 'quiz disponibile' : 'quiz disponibili'}
          </div>
        </div>
      </div>

      {/* Create/Edit Quiz Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg border border-gray-200 p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {editingQuiz ? 'Modifica Quiz' : 'Crea Nuovo Quiz'}
            </h2>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Titolo del Quiz *
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Es: Quiz sulle funzioni matematiche"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Descrizione
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
                  placeholder="Descrizione del quiz, argomenti trattati, obiettivi, etc."
                />
              </div>

              <div>
                <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-2">
                  Difficoltà
                </label>
                <select
                  id="difficulty"
                  name="difficulty"
                  value={formData.difficulty}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="facile">Facile</option>
                  <option value="medio">Medio</option>
                  <option value="difficile">Difficile</option>
                </select>
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false)
                    setEditingQuiz(null)
                    setFormData({ title: '', description: '', difficulty: 'medio' })
                  }}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-2"
                >
                  {loading ? (
                    <div className="loading-spinner h-4 w-4"></div>
                  ) : null}
                  <span>{editingQuiz ? 'Salva Modifiche' : 'Crea Quiz'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quizzes List */}
      <div className="space-y-4">
        {quizzes.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun quiz ancora creato</h3>
            <p className="text-gray-600 mb-6">
              Crea il tuo primo quiz per testare la conoscenza degli studenti
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="btn btn-primary"
            >
              Crea il Primo Quiz
            </button>
          </div>
        ) : (
          quizzes.map((quiz) => (
            <div key={quiz.id} className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{quiz.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      quiz.difficulty === 'facile'
                        ? 'bg-green-100 text-green-800'
                        : quiz.difficulty === 'medio'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {quiz.difficulty}
                    </span>
                    {quiz.is_active && (
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Attivo
                      </span>
                    )}
                  </div>

                  {quiz.description && (
                    <p className="text-gray-600 mb-3">{quiz.description}</p>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <FileText className="h-4 w-4" />
                      <span>{quiz.question_count} domande</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(quiz.created_at).toLocaleDateString('it-IT')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleCreateQuestions(quiz.id)}
                    className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                  >
                    {quiz.question_count === 0 ? 'Aggiungi Domande' : 'Modifica Domande'}
                  </button>
                  <button
                    onClick={() => handleEdit(quiz)}
                    className="p-1 text-gray-600 hover:text-gray-900"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(quiz.id)}
                    className="p-1 text-red-600 hover:text-red-900"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
