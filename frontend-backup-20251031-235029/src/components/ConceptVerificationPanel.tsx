'use client'

import { useState, useEffect } from 'react'
import {
  Brain,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  Target,
  Clock,
  Award,
  BookOpen,
  BarChart3,
  Play,
  RefreshCw
} from 'lucide-react'
import { useConceptKnowledge } from '@/hooks/useContentIndexing'
import { Concept, TestQuestion, UserProgress, ConceptMasteryVerification } from '@/types/indexing'

interface ConceptVerificationPanelProps {
  courseId: string
  userId: string
  onVerificationComplete?: (results: ConceptMasteryVerification[]) => void
}

interface VerificationSession {
  id: string
  conceptId: string
  conceptName: string
  questions: TestQuestion[]
  startedAt: string
  completedAt?: string
  answers: VerificationAnswer[]
  score?: number
  masteryLevel?: number
}

interface VerificationAnswer {
  questionId: string
  answer: string | string[]
  isCorrect: boolean
  timeTaken: number
  confidence: number
}

export function ConceptVerificationPanel({
  courseId,
  userId,
  onVerificationComplete
}: ConceptVerificationPanelProps) {
  const {
    concepts,
    testQuestions,
    isLoading,
    error,
    fetchConcepts,
    generateTestQuestions,
    updateConceptMastery
  } = useConceptKnowledge()

  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])
  const [verificationSession, setVerificationSession] = useState<VerificationSession | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [isVerifying, setIsVerifying] = useState(false)
  const [verificationHistory, setVerificationHistory] = useState<ConceptMasteryVerification[]>([])
  const [showResults, setShowResults] = useState(false)

  useEffect(() => {
    if (courseId) {
      fetchConcepts(courseId)
      loadVerificationHistory()
    }
  }, [courseId, fetchConcepts])

  const loadVerificationHistory = async () => {
    try {
      const response = await fetch(`/api/users/${userId}/concept-verifications`)
      if (response.ok) {
        const data = await response.json()
        setVerificationHistory(data.verifications || [])
      }
    } catch (error) {
      console.error('Error loading verification history:', error)
    }
  }

  const startVerification = async (conceptIds: string[]) => {
    try {
      setIsVerifying(true)
      setSelectedConcepts(conceptIds)

      // Generate test questions for selected concepts
      await generateTestQuestions(conceptIds, 5, 3) // 5 questions, medium difficulty

      if (testQuestions.length === 0) {
        throw new Error('No test questions generated')
      }

      // Create verification session
      const session: VerificationSession = {
        id: `session_${Date.now()}`,
        conceptId: conceptIds[0], // For now, focus on one concept at a time
        conceptName: concepts.find(c => c.id === conceptIds[0])?.name || 'Unknown Concept',
        questions: testQuestions.slice(0, 5), // Take first 5 questions
        startedAt: new Date().toISOString(),
        answers: []
      }

      setVerificationSession(session)
      setCurrentQuestionIndex(0)
      setShowResults(false)
    } catch (error) {
      console.error('Error starting verification:', error)
    } finally {
      setIsVerifying(false)
    }
  }

  const submitAnswer = (answer: string | string[], confidence: number) => {
    if (!verificationSession) return

    const currentQuestion = verificationSession.questions[currentQuestionIndex]
    const isCorrect = checkAnswer(currentQuestion, answer)

    const verificationAnswer: VerificationAnswer = {
      questionId: currentQuestion.id,
      answer,
      isCorrect,
      timeTaken: 30, // Would be calculated from actual time spent
      confidence
    }

    const updatedSession = {
      ...verificationSession,
      answers: [...verificationSession.answers, verificationAnswer]
    }

    setVerificationSession(updatedSession)

    if (currentQuestionIndex < verificationSession.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      completeVerification(updatedSession)
    }
  }

  const checkAnswer = (question: TestQuestion, answer: string | string[]): boolean => {
    if (Array.isArray(question.correct_answer)) {
      if (Array.isArray(answer)) {
        return question.correct_answer.every(correct => answer.includes(correct)) &&
               answer.length === question.correct_answer.length
      }
      return false
    } else {
      if (Array.isArray(answer)) {
        return answer.includes(question.correct_answer)
      }
      return answer.toLowerCase().trim() === question.correct_answer.toLowerCase().trim()
    }
  }

  const completeVerification = async (session: VerificationSession) => {
    const correctAnswers = session.answers.filter(a => a.isCorrect).length
    const totalQuestions = session.questions.length
    const score = (correctAnswers / totalQuestions) * 100

    // Calculate mastery level based on score and confidence
    const avgConfidence = session.answers.reduce((sum, a) => sum + a.confidence, 0) / session.answers.length
    const masteryLevel = Math.min(1, (score / 100) * (avgConfidence / 5))

    const completedSession = {
      ...session,
      completedAt: new Date().toISOString(),
      score,
      masteryLevel
    }

    setVerificationSession(completedSession)

    // Update concept mastery
    await updateConceptMastery(session.conceptId, masteryLevel)

    // Save verification result
    await saveVerificationResult(completedSession)

    setShowResults(true)
  }

  const saveVerificationResult = async (session: VerificationSession) => {
    try {
      const response = await fetch('/api/concept-verifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          concept_id: session.conceptId,
          session_data: session,
          mastery_level: session.masteryLevel,
          score: session.score
        })
      })

      if (response.ok) {
        const result = await response.json()
        if (onVerificationComplete) {
          onVerificationComplete([result.verification])
        }
      }
    } catch (error) {
      console.error('Error saving verification result:', error)
    }
  }

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
    if (level >= 0.6) return 'text-blue-600 bg-blue-50 border-blue-200'
    if (level >= 0.4) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getMasteryLabel = (level: number) => {
    if (level >= 0.8) return 'Maestro'
    if (level >= 0.6) return 'Competente'
    if (level >= 0.4) return 'In Progresso'
    return 'Da Iniziare'
  }

  const renderVerificationQuestion = () => {
    if (!verificationSession || currentQuestionIndex >= verificationSession.questions.length) {
      return null
    }

    const question = verificationSession.questions[currentQuestionIndex]
    const progress = ((currentQuestionIndex + 1) / verificationSession.questions.length) * 100

    return (
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-semibold text-gray-900">
              Domanda {currentQuestionIndex + 1} di {verificationSession.questions.length}
            </h4>
            <span className="text-sm text-gray-500">
              Concetto: {verificationSession.conceptName}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="mb-6">
          <div className="text-lg font-medium text-gray-900 mb-4">
            {question.question}
          </div>

          {question.type === 'multiple_choice' && question.options && (
            <div className="space-y-3">
              {question.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => submitAnswer(option, 3)} // Medium confidence default
                  className="w-full text-left p-4 rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200"
                >
                  {option}
                </button>
              ))}
            </div>
          )}

          {question.type === 'true_false' && (
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => submitAnswer('true', 3)}
                className="p-4 rounded-xl border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-all duration-200"
              >
                <CheckCircle className="h-6 w-6 text-green-600 mx-auto mb-2" />
                <span className="block text-center font-medium">Vero</span>
              </button>
              <button
                onClick={() => submitAnswer('false', 3)}
                className="p-4 rounded-xl border border-gray-200 hover:border-red-300 hover:bg-red-50 transition-all duration-200"
              >
                <XCircle className="h-6 w-6 text-red-600 mx-auto mb-2" />
                <span className="block text-center font-medium">Falso</span>
              </button>
            </div>
          )}

          {question.type === 'short_answer' && (
            <div className="space-y-4">
              <textarea
                placeholder="Scrivi la tua risposta..."
                className="w-full p-4 rounded-xl border border-gray-200 focus:border-blue-300 focus:ring-2 focus:ring-blue-100 transition-all duration-200"
                rows={3}
                id="shortAnswer"
              />
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Confidenza:</span>
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <button
                        key={level}
                        onClick={() => {
                          const textarea = document.getElementById('shortAnswer') as HTMLTextAreaElement
                          if (textarea.value.trim()) {
                            submitAnswer(textarea.value.trim(), level)
                          }
                        }}
                        className="w-8 h-8 rounded-full border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200"
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => {
                    const textarea = document.getElementById('shortAnswer') as HTMLTextAreaElement
                    if (textarea.value.trim()) {
                      submitAnswer(textarea.value.trim(), 3)
                    }
                  }}
                  className="btn btn-primary"
                >
                  Invia Risposta
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center text-sm text-gray-500">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4" />
            <span>{question.time_limit || 30}s</span>
          </div>
          <div className="flex items-center space-x-2">
            <Target className="h-4 w-4" />
            <span>{question.points} punti</span>
          </div>
        </div>
      </div>
    )
  }

  const renderVerificationResults = () => {
    if (!verificationSession) return null

    const correctAnswers = verificationSession.answers.filter(a => a.isCorrect).length
    const totalQuestions = verificationSession.questions.length
    const score = verificationSession.score || 0
    const masteryLevel = verificationSession.masteryLevel || 0

    return (
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="text-center mb-6">
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${getMasteryColor(masteryLevel)}`}>
            {masteryLevel >= 0.6 ? (
              <Award className="h-8 w-8" />
            ) : (
              <Brain className="h-8 w-8" />
            )}
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Verifica Completata!
          </h3>
          <p className="text-gray-600">
            Hai valutato la tua comprensione del concetto: <strong>{verificationSession.conceptName}</strong>
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="text-2xl font-bold text-blue-600">
              {score.toFixed(0)}%
            </div>
            <p className="text-sm text-gray-600">Punteggio</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="text-2xl font-bold text-green-600">
              {correctAnswers}/{totalQuestions}
            </div>
            <p className="text-sm text-gray-600">Risposte Corrette</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className={`text-2xl font-bold ${masteryLevel >= 0.6 ? 'text-green-600' : 'text-orange-600'}`}>
              {Math.round(masteryLevel * 100)}%
            </div>
            <p className="text-sm text-gray-600">Livello Mastery</p>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Livello di Mastery</span>
            <span className={`badge ${getMasteryColor(masteryLevel)}`}>
              {getMasteryLabel(masteryLevel)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${
                masteryLevel >= 0.8 ? 'bg-green-500' :
                masteryLevel >= 0.6 ? 'bg-blue-500' :
                masteryLevel >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${masteryLevel * 100}%` }}
            />
          </div>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={() => {
              setVerificationSession(null)
              setShowResults(false)
              setCurrentQuestionIndex(0)
            }}
            className="btn btn-primary flex-1"
          >
            <Play className="h-4 w-4 mr-2" />
            Nuova Verifica
          </button>
          <button
            onClick={() => setShowResults(false)}
            className="btn btn-secondary"
          >
            Chiudi
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Sistema di Verifica Comprensione
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Valuta il tuo livello di comprensione dei concetti chiave
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <BarChart3 className="h-4 w-4" />
            <span>{verificationHistory.length} verifiche completate</span>
          </div>
        </div>
      </div>

      {/* Concept Selection */}
      {!verificationSession && !showResults && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">
            Seleziona Concetti da Verificare
          </h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {concepts.filter(concept => concept.mastery_level !== undefined).map((concept) => (
              <div
                key={concept.id}
                className={`p-4 rounded-xl border transition-all duration-200 ${
                  selectedConcepts.includes(concept.id)
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedConcepts.includes(concept.id)}
                      onChange={() => {
                        const newSelected = selectedConcepts.includes(concept.id)
                          ? selectedConcepts.filter(id => id !== concept.id)
                          : [...selectedConcepts, concept.id]
                        setSelectedConcepts(newSelected)
                      }}
                      className="form-checkbox"
                    />
                    <div>
                      <div className="font-medium text-gray-900">
                        {concept.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {concept.category} • Difficoltà: {concept.difficulty}/5
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {concept.mastery_level && (
                      <div className={`badge ${getMasteryColor(concept.mastery_level)}`}>
                        {getMasteryLabel(concept.mastery_level)}
                      </div>
                    )}
                    <button
                      onClick={() => startVerification([concept.id])}
                      disabled={isVerifying}
                      className="btn btn-primary btn-sm"
                    >
                      {isVerifying ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {selectedConcepts.length > 0 && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={() => startVerification(selectedConcepts)}
                disabled={isVerifying}
                className="btn btn-primary"
              >
                {isVerifying ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Avvio Verifica...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Avvia Verifica ({selectedConcepts.length} concetti)
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Verification Question */}
      {verificationSession && !showResults && renderVerificationQuestion()}

      {/* Verification Results */}
      {showResults && renderVerificationResults()}

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger">
          <AlertCircle className="h-4 w-4 mr-2" />
          Errore: {error}
        </div>
      )}
    </div>
  )
}