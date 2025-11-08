'use client'

import { useState, useEffect, useRef } from 'react'
import {
  RotateCcw,
  Check,
  X,
  Clock,
  Target,
  TrendingUp,
  Calendar,
  Play,
  Pause,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

interface LearningCard {
  id: string
  course_id: string
  question: string
  answer: string
  card_type: string
  difficulty: number
  ease_factor: number
  interval_days: number
  repetitions: number
  next_review: string
  created_at: string
  last_reviewed?: string
  review_count: number
  total_quality: number
  context_tags: string[]
  source_material?: string
}

// Import API client
import { spacedRepetitionApi, LearningCard as ApiLearningCard, CreateCardRequest, CardReviewRequest, StudySession } from '@/utils/api'

// StudySession interface is now imported from API client

interface ReviewResult {
  card_id: string
  next_review: string
  interval_days: number
  ease_factor: number
  repetitions: number
  quality_rating: number
  review_session_id: string
}

// API_BASE_URL is now handled by the API client

export default function Flashcard({ courseId }: { courseId: string }) {
  const [session, setSession] = useState<StudySession | null>(null)
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isReviewing, setIsReviewing] = useState(false)
  const [startTime, setStartTime] = useState<number>(Date.now())
  const [reviewResults, setReviewResults] = useState<ReviewResult[]>([])
  const [sessionStats, setSessionStats] = useState({
    cardsReviewed: 0,
    correctReviews: 0,
    averageResponseTime: 0,
    startTime: Date.now()
  })

  const cardContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadStudySession()
  }, [courseId])

  const loadStudySession = async () => {
    try {
      setIsLoading(true)

      // For demo purposes, we'll use a demo user ID
      // In production, this would come from authentication
      const userId = "demo-user-123"

      const response = await spacedRepetitionApi.createSession(userId, courseId, 'mixed', 20)

      if (response.data) {
        setSession(response.data)
        setCurrentCardIndex(0)
        setIsFlipped(false)
      } else {
        console.error('Failed to load study session:', response.error)
      }
    } catch (error) {
      console.error('Error loading study session:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCardReview = async (qualityRating: number) => {
    if (!session || currentCardIndex >= session.cards.length) return

    const currentCard = session.cards[currentCardIndex]
    const responseTime = Date.now() - startTime

    try {
      setIsReviewing(true)

      const reviewData: CardReviewRequest = {
        card_id: currentCard.id,
        quality_rating: qualityRating,
        response_time_ms: responseTime,
        session_id: session.session_id
      }

      const response = await spacedRepetitionApi.reviewCard(reviewData)

      if (response.data) {
        setReviewResults(prev => [...prev, response.data])

        // Update session stats
        setSessionStats(prev => ({
          ...prev,
          cardsReviewed: prev.cardsReviewed + 1,
          correctReviews: prev.correctReviews + (qualityRating >= 3 ? 1 : 0),
          averageResponseTime: (
            (prev.averageResponseTime * prev.cardsReviewed + responseTime) /
            (prev.cardsReviewed + 1)
          )
        }))

        // Move to next card
        moveToNextCard()
      } else {
        console.error('Failed to review card:', response.error)
      }
    } catch (error) {
      console.error('Error reviewing card:', error)
    } finally {
      setIsReviewing(false)
    }
  }

  const moveToNextCard = () => {
    if (currentCardIndex < (session?.cards.length || 0) - 1) {
      setCurrentCardIndex(prev => prev + 1)
      setIsFlipped(false)
      setStartTime(Date.now())
    }
  }

  const moveToPreviousCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(prev => prev - 1)
      setIsFlipped(false)
      setStartTime(Date.now())
    }
  }

  const handleFlip = () => {
    setIsFlipped(!isFlipped)
  }

  const resetCard = () => {
    setIsFlipped(false)
    setStartTime(Date.now())
  }

  const getQualityButtonColor = (rating: number) => {
    switch (rating) {
      case 0: return 'bg-red-600 hover:bg-red-700'
      case 1: return 'bg-orange-600 hover:bg-orange-700'
      case 2: return 'bg-yellow-600 hover:bg-yellow-700'
      case 3: return 'bg-blue-600 hover:bg-blue-700'
      case 4: return 'bg-green-600 hover:bg-green-700'
      case 5: return 'bg-emerald-600 hover:bg-emerald-700'
      default: return 'bg-gray-600 hover:bg-gray-700'
    }
  }

  const getQualityButtonIcon = (rating: number) => {
    switch (rating) {
      case 0:
      case 1:
      case 2: return <X className="h-4 w-4" />
      case 3:
      case 4:
      case 5: return <Check className="h-4 w-4" />
      default: return null
    }
  }

  const getQualityLabel = (rating: number) => {
    switch (rating) {
      case 0: return 'Blackout'
      case 1: return 'Incorrect'
      case 2: return 'Incorrect'
      case 3: return 'Correct'
      case 4: return 'Correct'
      case 5: return 'Perfect'
      default: return ''
    }
  }

  const currentCard = session?.cards[currentCardIndex]
  const progress = session ? ((currentCardIndex + 1) / session.total_cards) * 100 : 0
  const isSessionComplete = session && currentCardIndex >= session.cards.length - 1 && isFlipped

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!session || session.cards.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Target className="h-10 w-10 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Nessuna scheda da studiare</h3>
        <p className="text-gray-600 mb-4">
          Non ci sono schede da ripassare in questo momento. Prova a generarne di nuove dai materiali del corso.
        </p>
        <button
          onClick={loadStudySession}
          className="btn btn-primary"
        >
          Ricarica
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Session Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Sessione di Ripasso</h2>
            <p className="text-sm text-gray-600">
              {session.cards.length} schede • {session.session_type}
            </p>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>
                {Math.round((Date.now() - sessionStats.startTime) / 1000 / 60)} min
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <Target className="h-4 w-4" />
              <span>{sessionStats.cardsReviewed}/{session.cards.length}</span>
            </div>
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-4 w-4" />
              <span>{sessionStats.correctReviews}/{sessionStats.cardsReviewed}</span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Flashcard */}
      <div className="flex justify-center">
        <div
          ref={cardContainerRef}
          className="relative w-full max-w-2xl"
          style={{ perspective: '1000px' }}
        >
          <div
            className={`relative h-80 bg-white rounded-lg border-2 border-gray-300 shadow-lg cursor-pointer transition-all duration-500 ${
              isFlipped ? 'rotate-y-180' : ''
            }`}
            onClick={handleFlip}
            style={{
              transformStyle: 'preserve-3d',
              transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
            }}
          >
            {/* Front (Question) */}
            <div
              className="absolute inset-0 p-8 flex flex-col items-center justify-center"
              style={{ backfaceVisibility: 'hidden' }}
            >
              <div className="text-center space-y-4">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {currentCard.card_type}
                  </span>
                  {currentCard.source_material && (
                    <span className="text-xs">
                      {currentCard.source_material}
                    </span>
                  )}
                </div>

                <h3 className="text-xl font-semibold text-gray-900">
                  {currentCard.question}
                </h3>

                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-3 w-3" />
                    <span>Rip: {currentCard.repetitions}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>{currentCard.interval_days}g</span>
                  </div>
                  <div>
                    Difficoltà: {Math.round(currentCard.difficulty * 100)}%
                  </div>
                </div>
              </div>

              <div className="absolute bottom-4 left-4 text-xs text-gray-400">
                Clicca per voltare
              </div>
            </div>

            {/* Back (Answer) */}
            <div
              className="absolute inset-0 p-8 flex flex-col items-center justify-center bg-green-50"
              style={{
                backfaceVisibility: 'hidden',
                transform: 'rotateY(180deg)'
              }}
            >
              <div className="text-center space-y-4">
                <div className="text-sm text-green-700 font-medium">
                  Risposta
                </div>

                <p className="text-lg text-gray-900">
                  {currentCard.answer}
                </p>

                {currentCard.context_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 justify-center">
                    {currentCard.context_tags.map((tag, index) => (
                      <span
                        key={index}
                        className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {currentCard.last_reviewed && (
                  <div className="text-xs text-gray-500">
                    Ultima revisione: {new Date(currentCard.last_reviewed).toLocaleDateString()}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-center space-x-4">
        <button
          onClick={moveToPreviousCard}
          disabled={currentCardIndex === 0}
          className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="h-4 w-4" />
          Precedente
        </button>

        <button
          onClick={resetCard}
          className="btn btn-secondary"
        >
          <RotateCcw className="h-4 w-4" />
          Reset
        </button>

        <button
          onClick={moveToNextCard}
          disabled={currentCardIndex >= session.cards.length - 1}
          className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Successiva
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {/* Quality Rating Buttons */}
      {isFlipped && !isSessionComplete && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 text-center">
            Quanto bene hai ricordato?
          </h3>
          <div className="grid grid-cols-6 gap-2">
            {[0, 1, 2, 3, 4, 5].map(rating => (
              <button
                key={rating}
                onClick={() => handleCardReview(rating)}
                disabled={isReviewing}
                className={`${getQualityButtonColor(rating)} text-white p-4 rounded-lg flex flex-col items-center space-y-1 hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {getQualityButtonIcon(rating)}
                <span className="text-xs font-medium">{rating}</span>
                <span className="text-xs">{getQualityLabel(rating)}</span>
              </button>
            ))}
          </div>
          {isReviewing && (
            <div className="mt-4 text-center text-sm text-gray-600">
              Elaborazione in corso...
            </div>
          )}
        </div>
      )}

      {/* Session Complete */}
      {isSessionComplete && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h3 className="text-xl font-semibold text-green-900 mb-2">
            Sessione Completata!
          </h3>
          <div className="space-y-2 text-green-700 mb-6">
            <p>Schede studiate: {sessionStats.cardsReviewed}</p>
            <p>Risposte corrette: {sessionStats.correctReviews}/{sessionStats.cardsReviewed}</p>
            <p>Tempo medio: {Math.round(sessionStats.averageResponseTime / 1000)}s per scheda</p>
            <p>Accuratezza: {Math.round((sessionStats.correctReviews / Math.max(1, sessionStats.cardsReviewed)) * 100)}%</p>
          </div>
          <div className="flex space-x-4 justify-center">
            <button
              onClick={loadStudySession}
              className="btn btn-primary"
            >
              Nuova Sessione
            </button>
            <button
              onClick={() => window.history.back()}
              className="btn btn-secondary"
            >
              Torna indietro
            </button>
          </div>
        </div>
      )}
    </div>
  )
}