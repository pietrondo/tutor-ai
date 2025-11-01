'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Brain,
  Clock,
  Target,
  TrendingUp,
  Zap,
  Award,
  BookOpen,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Calendar,
  BarChart3,
  Lightbulb,
  Activity,
  Star,
  Settings
} from 'lucide-react'

interface AdaptiveLearningSystemProps {
  userId: string
  courseId: string
  onLearningComplete?: (sessionData: LearningSession) => void
}

interface LearningSession {
  id: string
  startTime: string
  endTime?: string
  conceptsStudied: string[]
  strategiesUsed: LearningStrategy[]
  performance: {
    correctAnswers: number
    totalQuestions: number
    averageResponseTime: number
    confidenceLevel: number
  }
  metacognitiveFeedback: MetacognitiveFeedback[]
  retentionPrediction: number
}

interface LearningStrategy {
  type: 'spaced_repetition' | 'active_recall' | 'interleaving' | 'metacognitive' | 'elaboration'
  name: string
  description: string
  effectiveness: number
  currentMastery: number
  lastUsed: string
  nextReview: string
  interval: number // days
}

interface MetacognitiveFeedback {
  type: 'planning' | 'monitoring' | 'evaluation' | 'strategy'
  message: string
  timestamp: string
  impact: 'positive' | 'neutral' | 'negative'
}

interface SpacedRepetitionItem {
  conceptId: string
  conceptName: string
  interval: number
  repetitions: number
  easeFactor: number
  nextReview: string
  lastReview: string
  retentionProbability: number
}

interface ActiveRecallSession {
  conceptId: string
  questions: ActiveRecallQuestion[]
  performance: {
    correct: number
    total: number
    averageTime: number
  }
  confidenceBefore: number
  confidenceAfter: number
}

interface ActiveRecallQuestion {
  id: string
  question: string
  type: 'free_response' | 'multiple_choice' | 'true_false'
  difficulty: number
  timeLimit: number
  hints: string[]
}

interface InterleavingSet {
  concepts: string[]
  currentRound: number
  totalRounds: number
  performance: Record<string, number>
}

export function AdaptiveLearningSystem({
  userId,
  courseId,
  onLearningComplete
}: AdaptiveLearningSystemProps) {
  const [currentSession, setCurrentSession] = useState<LearningSession | null>(null)
  const [activeStrategy, setActiveStrategy] = useState<LearningStrategy | null>(null)
  const [spacedRepetitionItems, setSpacedRepetitionItems] = useState<SpacedRepetitionItem[]>([])
  const [activeRecallSession, setActiveRecallSession] = useState<ActiveRecallSession | null>(null)
  const [interleavingSet, setInterleavingSet] = useState<InterleavingSet | null>(null)
  const [metacognitiveInsights, setMetacognitiveInsights] = useState<MetacognitiveFeedback[]>([])
  const [learningProgress, setLearningProgress] = useState({
    conceptsMastered: 0,
    totalConcepts: 0,
    averageRetention: 0,
    studyStreak: 0
  })
  const [isSessionActive, setIsSessionActive] = useState(false)
  const [currentPhase, setCurrentPhase] = useState<'planning' | 'learning' | 'monitoring' | 'evaluation'>('planning')
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)

  useEffect(() => {
    initializeLearningSystem()
  }, [userId, courseId])

  const initializeLearningSystem = async () => {
    // Load user's learning data
    const items = await loadSpacedRepetitionItems()
    const insights = await loadMetacognitiveInsights()
    const progress = await loadLearningProgress()

    setSpacedRepetitionItems(items)
    setMetacognitiveInsights(insights)
    setLearningProgress(progress)
  }

  const loadSpacedRepetitionItems = async (): Promise<SpacedRepetitionItem[]> => {
    // Simulate API call
    return [
      {
        conceptId: 'react-hooks',
        conceptName: 'React Hooks',
        interval: 3,
        repetitions: 2,
        easeFactor: 2.5,
        nextReview: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
        lastReview: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        retentionProbability: 0.85
      },
      {
        conceptId: 'typescript',
        conceptName: 'TypeScript Basics',
        interval: 1,
        repetitions: 1,
        easeFactor: 2.0,
        nextReview: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
        lastReview: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        retentionProbability: 0.72
      }
    ]
  }

  const loadMetacognitiveInsights = async (): Promise<MetacognitiveFeedback[]> => {
    return [
      {
        type: 'planning',
        message: 'Ottima pianificazione! Hai identificato bene i concetti da rivedere.',
        timestamp: new Date().toISOString(),
        impact: 'positive'
      },
      {
        type: 'monitoring',
        message: 'Stai monitorando bene il tuo progresso. Continua a controllare la tua comprensione.',
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        impact: 'positive'
      }
    ]
  }

  const loadLearningProgress = async () => ({
    conceptsMastered: 12,
    totalConcepts: 25,
    averageRetention: 0.78,
    studyStreak: 7
  })

  const startSpacedRepetitionSession = (item: SpacedRepetitionItem) => {
    const session: LearningSession = {
      id: `sr_${Date.now()}`,
      startTime: new Date().toISOString(),
      conceptsStudied: [item.conceptId],
      strategiesUsed: [{
        type: 'spaced_repetition',
        name: 'Spaced Repetition',
        description: 'Review concepts at optimal intervals for long-term retention',
        effectiveness: 0.89,
        currentMastery: item.retentionProbability,
        lastUsed: new Date().toISOString(),
        nextReview: item.nextReview,
        interval: item.interval
      }],
      performance: {
        correctAnswers: 0,
        totalQuestions: 0,
        averageResponseTime: 0,
        confidenceLevel: 0.5
      },
      metacognitiveFeedback: [],
      retentionPrediction: item.retentionProbability
    }

    setCurrentSession(session)
    setIsSessionActive(true)
    setCurrentPhase('learning')

    // Generate active recall questions for this concept
    generateActiveRecallQuestions(item.conceptId)
  }

  const generateActiveRecallQuestions = async (conceptId: string) => {
    const questions: ActiveRecallQuestion[] = [
      {
        id: 'q1',
        question: 'Spiega con parole tue il concetto principale di React Hooks',
        type: 'free_response',
        difficulty: 3,
        timeLimit: 120,
        hints: ['Pensa ai lifecycle methods', 'Considera lo stato locale']
      },
      {
        id: 'q2',
        question: 'Qual è la differenza tra useState e useEffect?',
        type: 'free_response',
        difficulty: 4,
        timeLimit: 90,
        hints: ['Uno gestisce lo stato', 'l\'altro gestisce effetti collaterali']
      }
    ]

    const session: ActiveRecallSession = {
      conceptId,
      questions,
      performance: { correct: 0, total: questions.length, averageTime: 0 },
      confidenceBefore: 0.6,
      confidenceAfter: 0.6
    }

    setActiveRecallSession(session)
  }

  const handleAnswer = (questionId: string, answer: string, timeTaken: number) => {
    if (!currentSession || !activeRecallSession) return

    // Simulate answer evaluation
    const isCorrect = Math.random() > 0.3

    // Update performance
    const updatedSession = {
      ...currentSession,
      performance: {
        ...currentSession.performance,
        correctAnswers: currentSession.performance.correctAnswers + (isCorrect ? 1 : 0),
        totalQuestions: currentSession.performance.totalQuestions + 1,
        averageResponseTime: (currentSession.performance.averageResponseTime + timeTaken) / 2
      }
    }

    setCurrentSession(updatedSession)

    // Update active recall session
    const updatedRecallSession = {
      ...activeRecallSession,
      performance: {
        ...activeRecallSession.performance,
        correct: activeRecallSession.performance.correct + (isCorrect ? 1 : 0),
        averageTime: (activeRecallSession.performance.averageTime + timeTaken) / 2
      }
    }

    setActiveRecallSession(updatedRecallSession)

    // Generate metacognitive feedback
    generateMetacognitiveFeedback(isCorrect, timeTaken)
  }

  const generateMetacognitiveFeedback = (isCorrect: boolean, timeTaken: number) => {
    let feedback: MetacognitiveFeedback

    if (isCorrect && timeTaken < 60) {
      feedback = {
        type: 'evaluation',
        message: 'Eccellente! Risposta corretta e veloce. Mostra buona padronanza del concetto.',
        timestamp: new Date().toISOString(),
        impact: 'positive'
      }
    } else if (isCorrect && timeTaken > 120) {
      feedback = {
        type: 'monitoring',
        message: 'Risposta corretta, ma hai impiegato tempo. Prova a rendere il processo più automatico.',
        timestamp: new Date().toISOString(),
        impact: 'neutral'
      }
    } else {
      feedback = {
        type: 'strategy',
        message: 'Ripassa il concetto usando esempi pratici. Prova a spiegare ad alta voce.',
        timestamp: new Date().toISOString(),
        impact: 'negative'
      }
    }

    setMetacognitiveInsights(prev => [...prev, feedback])
  }

  const startInterleavingSession = () => {
    // Mix different concepts for interleaving practice
    const concepts = spacedRepetitionItems.slice(0, 3).map(item => item.conceptId)

    const interleavingSession: InterleavingSet = {
      concepts,
      currentRound: 1,
      totalRounds: 3,
      performance: {}
    }

    setInterleavingSet(interleavingSession)
    setIsSessionActive(true)
    setCurrentPhase('learning')
  }

  const completeLearningSession = () => {
    if (!currentSession) return

    const completedSession: LearningSession = {
      ...currentSession,
      endTime: new Date().toISOString(),
      retentionPrediction: calculateRetentionPrediction(currentSession)
    }

    setCurrentSession(null)
    setIsSessionActive(false)
    setCurrentPhase('evaluation')
    setActiveRecallSession(null)
    setInterleavingSet(null)

    if (onLearningComplete) {
      onLearningComplete(completedSession)
    }

    // Update spaced repetition intervals based on performance
    updateSpacedRepetitionIntervals(completedSession)
  }

  const calculateRetentionPrediction = (session: LearningSession): number => {
    const accuracy = session.performance.correctAnswers / session.performance.totalQuestions
    const confidenceBonus = session.performance.confidenceLevel * 0.2
    const timePenalty = session.performance.averageResponseTime > 90 ? 0.1 : 0

    return Math.min(1, accuracy + confidenceBonus - timePenalty)
  }

  const updateSpacedRepetitionIntervals = (session: LearningSession) => {
    // Update items based on performance (simplified SM-2 algorithm)
    const updatedItems = spacedRepetitionItems.map(item => {
      if (session.conceptsStudied.includes(item.conceptId)) {
        const accuracy = session.performance.correctAnswers / session.performance.totalQuestions

        if (accuracy >= 0.8) {
          return {
            ...item,
            interval: Math.round(item.interval * item.easeFactor),
            repetitions: item.repetitions + 1,
            easeFactor: Math.min(2.5, item.easeFactor + 0.1),
            nextReview: new Date(Date.now() + item.interval * item.easeFactor * 24 * 60 * 60 * 1000).toISOString(),
            lastReview: new Date().toISOString(),
            retentionProbability: Math.min(1, item.retentionProbability + 0.1)
          }
        } else {
          return {
            ...item,
            interval: Math.max(1, Math.round(item.interval * 0.5)),
            easeFactor: Math.max(1.3, item.easeFactor - 0.2),
            nextReview: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            lastReview: new Date().toISOString(),
            retentionProbability: Math.max(0.3, item.retentionProbability - 0.1)
          }
        }
      }
      return item
    })

    setSpacedRepetitionItems(updatedItems)
  }

  const getRecommendations = () => {
    const dueItems = spacedRepetitionItems.filter(item =>
      new Date(item.nextReview) <= new Date()
    )

    if (dueItems.length > 0) {
      return {
        priority: 'high',
        message: `Hai ${dueItems.length} concetti da rivedere oggi per ottimizzare la retention`,
        action: 'start_spaced_repetition',
        items: dueItems
      }
    }

    return {
      priority: 'medium',
      message: 'Prova l\'interleaving practice per consolidare i concetti appresi',
      action: 'start_interleaving',
      items: spacedRepetitionItems.slice(0, 3)
    }
  }

  const recommendations = getRecommendations()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Sistema di Apprendimento Adattivo
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Basato su strategie cognitive evidence-based: Spaced Repetition, Active Recall, Interleaving
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            className="btn btn-secondary btn-sm"
          >
            <Settings className="h-4 w-4 mr-2" />
            Opzioni Avanzate
          </button>
        </div>

        {/* Learning Progress Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-xl">
            <div className="text-2xl font-bold text-blue-600">
              {learningProgress.conceptsMastered}/{learningProgress.totalConcepts}
            </div>
            <p className="text-xs text-gray-600">Concetti Dominati</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-xl">
            <div className="text-2xl font-bold text-green-600">
              {Math.round(learningProgress.averageRetention * 100)}%
            </div>
            <p className="text-xs text-gray-600">Retention Media</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-xl">
            <div className="text-2xl font-bold text-purple-600">
              {learningProgress.studyStreak}
            </div>
            <p className="text-xs text-gray-600">Giorni di Studio</p>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-xl">
            <div className="text-2xl font-bold text-orange-600">
              {spacedRepetitionItems.filter(item => new Date(item.nextReview) <= new Date()).length}
            </div>
            <p className="text-xs text-gray-600">Da Rivedere Oggi</p>
          </div>
        </div>
      </div>

      {/* Current Phase Indicator */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900">Fase di Apprendimento Corrente</h4>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            currentPhase === 'planning' ? 'bg-blue-100 text-blue-800' :
            currentPhase === 'learning' ? 'bg-green-100 text-green-800' :
            currentPhase === 'monitoring' ? 'bg-yellow-100 text-yellow-800' :
            'bg-purple-100 text-purple-800'
          }`}>
            {currentPhase === 'planning' ? 'Pianificazione' :
             currentPhase === 'learning' ? 'Apprendimento Attivo' :
             currentPhase === 'monitoring' ? 'Monitoraggio' : 'Valutazione'}
          </div>
        </div>

        <div className="flex space-x-2">
          {['planning', 'learning', 'monitoring', 'evaluation'].map((phase, index) => (
            <div
              key={phase}
              className={`flex-1 h-2 rounded-full ${
                currentPhase === phase ? 'bg-blue-600' :
                index < ['planning', 'learning', 'monitoring', 'evaluation'].indexOf(currentPhase) ? 'bg-green-500' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-4">
          <Lightbulb className="h-5 w-5 text-yellow-600" />
          <h4 className="font-semibold text-gray-900">Raccomandazioni Cognitive</h4>
        </div>

        <div className={`p-4 rounded-lg border ${
          recommendations.priority === 'high' ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'
        }`}>
          <p className={`text-sm mb-3 ${
            recommendations.priority === 'high' ? 'text-red-800' : 'text-blue-800'
          }`}>
            {recommendations.message}
          </p>

          {recommendations.action === 'start_spaced_repetition' && (
            <div className="space-y-3">
              {recommendations.items.slice(0, 3).map((item) => (
                <div key={item.conceptId} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{item.conceptName}</div>
                    <div className="text-xs text-gray-500">
                      Retention: {Math.round(item.retentionProbability * 100)}% • Interval: {item.interval} days
                    </div>
                  </div>
                  <button
                    onClick={() => startSpacedRepetitionSession(item)}
                    disabled={isSessionActive}
                    className="btn btn-primary btn-sm"
                  >
                    Inizia Review
                  </button>
                </div>
              ))}
            </div>
          )}

          {recommendations.action === 'start_interleaving' && (
            <button
              onClick={startInterleavingSession}
              disabled={isSessionActive}
              className="btn btn-primary"
            >
              <Activity className="h-4 w-4 mr-2" />
              Inizia Interleaving Practice
            </button>
          )}
        </div>
      </div>

      {/* Active Learning Session */}
      {isSessionActive && currentSession && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">
              Sessione di {activeStrategy?.name || 'Apprendimento'}
            </h4>
            <button
              onClick={completeLearningSession}
              className="btn btn-secondary btn-sm"
            >
              Completa Sessione
            </button>
          </div>

          {/* Active Recall Questions */}
          {activeRecallSession && (
            <div className="space-y-4">
              {activeRecallSession.questions.map((question) => (
                <div key={question.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      {question.question}
                    </span>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <Clock className="h-4 w-4" />
                      <span>{question.timeLimit}s</span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <textarea
                      placeholder="Scrivi la tua risposta..."
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows={3}
                    />
                    <div className="mt-2 flex justify-between items-center">
                      <div className="flex space-x-2">
                        {question.hints.map((hint, index) => (
                          <span key={index} className="text-xs text-gray-500 bg-yellow-100 px-2 py-1 rounded">
                            💡 {hint}
                          </span>
                        ))}
                      </div>
                      <button
                        onClick={() => handleAnswer(question.id, 'sample answer', 45)}
                        className="btn btn-primary btn-sm"
                      >
                        Invia Risposta
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Performance Metrics */}
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">
                {currentSession.performance.correctAnswers}/{currentSession.performance.totalQuestions}
              </div>
              <p className="text-xs text-gray-600">Risposte Corrette</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">
                {Math.round(currentSession.performance.averageResponseTime)}s
              </div>
              <p className="text-xs text-gray-600">Tempo Medio</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">
                {Math.round(currentSession.performance.confidenceLevel * 100)}%
              </div>
              <p className="text-xs text-gray-600">Livello Confidenza</p>
            </div>
          </div>
        </div>
      )}

      {/* Metacognitive Insights */}
      {metacognitiveInsights.length > 0 && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Brain className="h-5 w-5 text-purple-600" />
            <h4 className="font-semibold text-gray-900">Insights Metacognitivi</h4>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto">
            {metacognitiveInsights.slice(-5).reverse().map((insight, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  insight.impact === 'positive' ? 'bg-green-50 border-green-200' :
                  insight.impact === 'negative' ? 'bg-red-50 border-red-200' :
                  'bg-yellow-50 border-yellow-200'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {insight.impact === 'positive' ? (
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                  ) : insight.impact === 'negative' ? (
                    <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                  ) : (
                    <Activity className="h-4 w-4 text-yellow-600 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className={`text-sm ${
                      insight.impact === 'positive' ? 'text-green-800' :
                      insight.impact === 'negative' ? 'text-red-800' : 'text-yellow-800'
                    }`}>
                      {insight.message}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(insight.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Options */}
      {showAdvancedOptions && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Opzioni Avanzate</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Intervallo di Spaced Repetition
              </label>
              <select className="form-input">
                <option>Conservativo (fattore 1.3)</option>
                <option>Standard (fattore 2.5)</option>
                <option>Aggressivo (fattore 3.0)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficoltà Adattiva
              </label>
              <select className="form-input">
                <option>Fissa</option>
                <option>Adattiva Basata su Performance</option>
                <option>Adattiva Basata su Confidenza</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}