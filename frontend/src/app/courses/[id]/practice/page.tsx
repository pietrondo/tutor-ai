'use client'

import { useState, useEffect, Suspense, type FormEvent } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Brain, Target, Plus, BarChart3, Settings } from 'lucide-react'
import Flashcard from '@/components/Flashcard'

interface Course {
  id: string
  name: string
  subject: string
  description: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
}

interface Analytics {
  period_days: number
  card_statistics: {
    total_cards: number
    due_cards: number
    avg_difficulty: number
    avg_quality: number
  }
  review_statistics: {
    total_reviews: number
    avg_quality: number
    avg_response_time_ms: number
    correct_reviews: number
    accuracy_rate: number
  }
  learning_curve: Array<{
    date: string
    avg_quality: number
    reviews_count: number
  }>
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8001'

function PracticeContent() {
  const params = useParams()
  const courseId = params.id as string

  const [course, setCourse] = useState<Course | null>(null)
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [activeTab, setActiveTab] = useState<'practice' | 'analytics' | 'manage'>('practice')
  const [loading, setLoading] = useState(true)
  const [showCreateCard, setShowCreateCard] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  // Form state for creating cards
  const [newCard, setNewCard] = useState({
    question: '',
    answer: '',
    card_type: 'basic',
    context_tags: ''
  })

  useEffect(() => {
    loadCourse()
    loadAnalytics()
  }, [courseId])

  const loadCourse = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setCourse(data.course)
      }
    } catch (error) {
      console.error('Error loading course:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/spaced-repetition/analytics/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setAnalytics(data)
      }
    } catch (error) {
      console.error('Error loading analytics:', error)
    }
  }

  const handleCreateCard = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!newCard.question.trim() || !newCard.answer.trim()) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/spaced-repetition/card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          question: newCard.question.trim(),
          answer: newCard.answer.trim(),
          card_type: newCard.card_type,
          context_tags: newCard.context_tags.split(',').map(tag => tag.trim()).filter(Boolean)
        })
      })

      if (response.ok) {
        setNewCard({ question: '', answer: '', card_type: 'basic', context_tags: '' })
        setShowCreateCard(false)
        loadAnalytics() // Refresh analytics
      } else {
        console.error('Failed to create card')
      }
    } catch (error) {
      console.error('Error creating card:', error)
    }
  }

  const handleAutoGenerateCards = async () => {
    setIsGenerating(true)
    try {
      // Get course materials to use as content source
      const booksResponse = await fetch(`${API_BASE_URL}/courses/${courseId}/books`)
      if (!booksResponse.ok) {
        throw new Error('Failed to fetch course materials')
      }

      const books = await booksResponse.json()

      if (books.length === 0) {
        alert('Nessun materiale trovato per questo corso. Carica prima dei documenti per generare schede automaticamente.')
        setIsGenerating(false)
        return
      }

      // Generate cards from the first available book
      const selectedBook = books[0]
      const response = await fetch(`${API_BASE_URL}/api/spaced-repetition/generate-from-sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          source_material: selectedBook.id,
          max_cards: 10 // Generate up to 10 cards
        })
      })

      if (response.ok) {
        const result = await response.json()
        alert(`Generate con successo ${result.cards_generated || 0} schede dal materiale "${selectedBook.title}"`)
        loadAnalytics() // Refresh analytics
      } else {
        const error = await response.text()
        console.error('Failed to generate cards:', error)
        alert('Errore nella generazione delle schede. Riprova più tardi.')
      }
    } catch (error) {
      console.error('Error generating cards:', error)
      alert('Errore nella generazione delle schede. Assicurati di avere caricato dei materiali nel corso.')
    } finally {
      setIsGenerating(false)
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
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Corso non trovato</h2>
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

          <div className="flex items-center space-x-3">
            <button
              onClick={handleAutoGenerateCards}
              disabled={isGenerating}
              className="btn btn-secondary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Brain className="h-4 w-4" />
              <span>{isGenerating ? 'Generazione...' : 'Genera con AI'}</span>
            </button>

            <button
              onClick={() => setShowCreateCard(true)}
              className="btn btn-primary flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Nuova Scheda</span>
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Practice Spaced Repetition</h1>
          <p className="text-lg text-gray-600">{course.name}</p>

          {/* Quick Stats */}
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-blue-600 mb-1">
                  <Target className="h-5 w-5" />
                  <span className="font-medium">Schede Totali</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">
                  {analytics.card_statistics.total_cards}
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-green-600 mb-1">
                  <Brain className="h-5 w-5" />
                  <span className="font-medium">Da Ripassare</span>
                </div>
                <div className="text-2xl font-bold text-green-900">
                  {analytics.card_statistics.due_cards}
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-purple-600 mb-1">
                  <BarChart3 className="h-5 w-5" />
                  <span className="font-medium">Accuratezza</span>
                </div>
                <div className="text-2xl font-bold text-purple-900">
                  {Math.round(analytics.review_statistics.accuracy_rate * 100)}%
                </div>
              </div>

              <div className="bg-orange-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-orange-600 mb-1">
                  <Settings className="h-5 w-5" />
                  <span className="font-medium">Media Qualità</span>
                </div>
                <div className="text-2xl font-bold text-orange-900">
                  {analytics.review_statistics.avg_quality.toFixed(1)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Card Modal */}
      {showCreateCard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="max-w-md w-full bg-white rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Crea Nuova Scheda</h3>

            <form onSubmit={handleCreateCard} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Domanda
                </label>
                <textarea
                  value={newCard.question}
                  onChange={(e) => setNewCard({ ...newCard, question: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Inserisci la domanda..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Risposta
                </label>
                <textarea
                  value={newCard.answer}
                  onChange={(e) => setNewCard({ ...newCard, answer: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={4}
                  placeholder="Inserisci la risposta..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo Scheda
                </label>
                <select
                  value={newCard.card_type}
                  onChange={(e) => setNewCard({ ...newCard, card_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="basic">Base</option>
                  <option value="cloze">Completa</option>
                  <option value="concept">Concetto</option>
                  <option value="application">Applicazione</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tag Contestuali (separati da virgola)
                </label>
                <input
                  type="text"
                  value={newCard.context_tags}
                  onChange={(e) => setNewCard({ ...newCard, context_tags: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="es: capitolo1, definizioni, importante"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateCard(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Crea Scheda
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Practice Session */}
      {activeTab === 'practice' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Sessione di Studio</h2>
            <p className="text-sm text-gray-600 mb-4">
              Pratica con le schede utilizzando l'algoritmo di ripetizione spaziata per massimizzare la ritenzione.
            </p>
            <Flashcard courseId={courseId} />
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && analytics && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Analisi di Apprendimento</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Statistics Overview */}
            <div>
              <h3 className="text-md font-medium text-gray-800 mb-3">Statistiche Schede</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Totali:</span>
                  <span className="font-medium">{analytics.card_statistics.total_cards}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Da ripassare:</span>
                  <span className="font-medium">{analytics.card_statistics.due_cards}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Difficoltà media:</span>
                  <span className="font-medium">{(analytics.card_statistics.avg_difficulty * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Qualità media:</span>
                  <span className="font-medium">{analytics.card_statistics.avg_quality.toFixed(1)}/5</span>
                </div>
              </div>
            </div>

            {/* Review Statistics */}
            <div>
              <h3 className="text-md font-medium text-gray-800 mb-3">Statistiche Ripasso</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Ripassi totali:</span>
                  <span className="font-medium">{analytics.review_statistics.total_reviews}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tempo medio:</span>
                  <span className="font-medium">{(analytics.review_statistics.avg_response_time_ms / 1000).toFixed(1)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Corrette:</span>
                  <span className="font-medium">{analytics.review_statistics.correct_reviews}/{analytics.review_statistics.total_reviews}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Accuratezza:</span>
                  <span className="font-medium">{(analytics.review_statistics.accuracy_rate * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Learning Curve */}
          {analytics.learning_curve.length > 0 && (
            <div className="mt-6">
              <h3 className="text-md font-medium text-gray-800 mb-3">Andamento Apprendimento</h3>
              <div className="space-y-2">
                {analytics.learning_curve.slice(-7).map((point, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">{point.date}</span>
                    <div className="flex items-center space-x-4">
                      <span className="text-gray-800">Qualità: {point.avg_quality.toFixed(1)}</span>
                      <span className="text-gray-800">Ripassi: {point.reviews_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <nav className="flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('practice')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'practice'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Practice
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analytics'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Analytics
          </button>
        </nav>
      </div>
    </div>
  )
}

export default function PracticePage() {
  return (
    <Suspense fallback={
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    }>
      <PracticeContent />
    </Suspense>
  )
}
