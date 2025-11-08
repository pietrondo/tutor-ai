'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Clock, Target, TrendingUp, Calendar, Play, Pause,
  RotateCcw, CheckCircle, XCircle, AlertCircle
} from 'lucide-react'

// Import CLE API clients
import { spacedRepetitionApi, LearningCard } from '@/utils/api'
import { activeRecallApi, Question } from '@/utils/api'
import { dualCodingApi } from '@/utils/api'
import { interleavedPracticeApi } from '@/utils/api'
import { metacognitionApi } from '@/utils/api'
import { elaborationNetworkApi } from '@/utils/api'

// Types
interface SessionStats {
  totalCards: number
  cardsStudied: number
  correctAnswers: number
  averageResponseTime: number
  sessionDuration: number
  streakDays: number
}

interface CLEPhase {
  id: string
  name: string
  description: string
  status: 'idle' | 'active' | 'completed' | 'error'
  progress: number
  icon: React.ReactNode
  color: string
}

export default function CLEPracticePage({ params }: { params: { id: string } }) {
  const courseId = params.id
  const [activeTab, setActiveTab] = useState('spaced-repetition')
  const [sessionStats, setSessionStats] = useState<SessionStats>({
    totalCards: 0,
    cardsStudied: 0,
    correctAnswers: 0,
    averageResponseTime: 0,
    sessionDuration: 0,
    streakDays: 0
  })

  // Spaced Repetition state
  const [currentCard, setCurrentCard] = useState<LearningCard | null>(null)
  const [isFlipped, setIsFlipped] = useState(false)
  const [showAnswer, setShowAnswer] = useState(false)
  const [responseStartTime, setResponseStartTime] = useState<number>(0)

  // Active Recall state
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [feedback, setFeedback] = useState<string>('')

  // Dual Coding state
  const [visualElements, setVisualElements] = useState<any[]>([])
  const [selectedVisualType, setSelectedVisualType] = useState('mind_map')

  // Metacognition state
  const [reflectionPrompt, setReflectionPrompt] = useState('')
  const [reflectionResponse, setReflectionResponse] = useState('')

  // Network state
  const [networkVisualization, setNetworkVisualization] = useState<any>(null)

  const CLEPhases: CLEPhase[] = [
    {
      id: 'spaced-repetition',
      name: 'Spaced Repetition',
      description: 'Algorithmic memory retention with enhanced SM-2',
      status: 'idle',
      progress: 0,
      icon: <Clock className="h-4 w-4" />,
      color: 'blue'
    },
    {
      id: 'active-recall',
      name: 'Active Recall',
      description: 'Systematic knowledge retrieval practice',
      status: 'idle',
      progress: 0,
      icon: <Target className="h-4 w-4" />,
      color: 'green'
    },
    {
      id: 'dual-coding',
      name: 'Dual Coding',
      description: 'Visual-verbal integration learning',
      status: 'idle',
      progress: 0,
      icon: <RotateCcw className="h-4 w-4" />,
      color: 'purple'
    },
    {
      id: 'interleaved-practice',
      name: 'Interleaved Practice',
      description: 'Mixed concept practice scheduling',
      status: 'idle',
      progress: 0,
      icon: <TrendingUp className="h-4 w-4" />,
      color: 'orange'
    },
    {
      id: 'metacognition',
      name: 'Metacognition',
      description: 'Self-regulation and reflection',
      status: 'idle',
      progress: 0,
      icon: <AlertCircle className="h-4 w-4" />,
      color: 'red'
    },
    {
      id: 'elaboration-network',
      name: 'Elaboration Network',
      description: 'Knowledge integration and transfer',
      status: 'idle',
      progress: 0,
      icon: <Calendar className="h-4 w-4" />,
      color: 'indigo'
    }
  ]

  // Initialize session
  useEffect(() => {
    initializeSession()
  }, [courseId])

  const initializeSession = async () => {
    try {
      // Create spaced repetition session
      const sessionResponse = await spacedRepetitionApi.createSession(
        'demo-user', // In production, get from auth
        courseId,
        'mixed',
        10
      )

      if (sessionResponse.data) {
        // Get first card
        const cardsResponse = await spacedRepetitionApi.getDueCards(
          courseId,
          'demo-user',
          1
        )

        if (cardsResponse.data && cardsResponse.data.length > 0) {
          setCurrentCard(cardsResponse.data[0])
          setSessionStats(prev => ({
            ...prev,
            totalCards: 10 // Get actual count from API
          }))
        }
      }

      // Load visual elements
      const visualResponse = await dualCodingApi.getVisualElements()
      if (visualResponse.data) {
        setVisualElements(visualResponse.data)
      }

    } catch (error) {
      console.error('Error initializing session:', error)
    }
  }

  // Spaced Repetition functions
  const handleCardFlip = () => {
    setIsFlipped(!isFlipped)
    setShowAnswer(true)
    setResponseStartTime(Date.now())
  }

  const handleQualityRating = async (quality: number) => {
    if (!currentCard) return

    try {
      const responseTime = Date.now() - responseStartTime
      const reviewResponse = await spacedRepetitionApi.reviewCard({
        card_id: currentCard.id,
        quality_rating: quality,
        response_time_ms: responseTime,
        session_id: 'session-id' // Get from session
      })

      if (reviewResponse.data) {
        // Move to next card
        moveToNextCard()
      }
    } catch (error) {
      console.error('Error submitting review:', error)
    }

    setIsFlipped(false)
    setShowAnswer(false)
  }

  const moveToNextCard = async () => {
    try {
      const cardsResponse = await spacedRepetitionApi.getDueCards(
        courseId,
        'demo-user',
        1
      )

      if (cardsResponse.data && cardsResponse.data.length > 0) {
        setCurrentCard(cardsResponse.data[0])
        setSessionStats(prev => ({
          ...prev,
          cardsStudied: prev.cardsStudied + 1
        }))
      } else {
        // Session completed
        setCurrentCard(null)
        setSessionStats(prev => ({
          ...prev,
          progress: 100
        }))
      }
    } catch (error) {
      console.error('Error getting next card:', error)
    }
  }

  // Active Recall functions
  const handleStartActiveRecallSession = async () => {
    try {
      const sessionResponse = await activeRecallApi.startSession(
        'demo-user',
        courseId,
        5
      )

      if (sessionResponse.data) {
        // Get first question
        const questionResponse = await activeRecallApi.getNextQuestion(
          sessionResponse.data.session_id
        )

        if (questionResponse.data) {
          setCurrentQuestion(questionResponse.data)
          setUserAnswer('')
          setFeedback('')
        }
      }
    } catch (error) {
      console.error('Error starting active recall session:', error)
    }
  }

  const handleSubmitAnswer = async () => {
    if (!currentQuestion) return

    try {
      const response = await activeRecallApi.submitAnswer({
        question_id: currentQuestion.id,
        user_answer: userAnswer,
        response_time_ms: 5000, // Calculate actual time
        confidence_level: 3
      })

      if (response.data) {
        // Get next question or complete session
        const nextQuestionResponse = await activeRecallApi.getNextQuestion(
          'session-id' // Get from session
        )

        if (nextQuestionResponse.data) {
          setCurrentQuestion(nextQuestionResponse.data)
          setUserAnswer('')
          setFeedback('')
        } else {
          // Session completed
          setCurrentQuestion(null)
          setFeedback('Session completed! Great job!')
        }
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
      setFeedback('Error submitting answer. Please try again.')
    }
  }

  // Dual Coding functions
  const handleCreateDualCoding = async () => {
    try {
      const content = currentCard?.question || 'Sample content for dual coding'
      const response = await dualCodingApi.createContent({
        content: content,
        content_type: 'text',
        target_audience: 'intermediate',
        learning_style: 'balanced'
      })

      if (response.data) {
        // Handle successful creation
        console.log('Dual coding content created:', response.data)
      }
    } catch (error) {
      console.error('Error creating dual coding content:', error)
    }
  }

  // Metacognition functions
  const handleStartReflection = async () => {
    try {
      const reflectionContext = {
        current_activity: 'practice_session',
        recent_performance: sessionStats,
        learning_objectives: ['improve retention', 'deepen understanding']
      }

      const response = await metacognitionApi.createReflectionActivity(
        'demo-user',
        courseId,
        'performance',
        reflectionContext
      )

      if (response.data) {
        setReflectionPrompt(response.data.reflection_prompts[0] || 'How did you feel about this practice session?')
      }
    } catch (error) {
      console.error('Error creating reflection activity:', error)
    }
  }

  // Network functions
  const handleVisualizeNetwork = async () => {
    try {
      const knowledgeBase = {
        concepts: [
          { id: 'concept1', name: 'Sample Concept', description: 'A sample concept' }
        ],
        connections: []
      }

      const networkResponse = await elaborationNetworkApi.buildNetwork(
        'demo-user',
        courseId,
        knowledgeBase,
        ['deep_understanding']
      )

      if (networkResponse.data) {
        const visualizationResponse = await elaborationNetworkApi.visualizeNetwork(
          networkResponse.data.network_id
        )

        if (visualizationResponse.data) {
          setNetworkVisualization(visualizationResponse.data)
        }
      }
    } catch (error) {
      console.error('Error visualizing network:', error)
    }
  }

  const getPhaseColor = (status: string) => {
    const colors: { [key: string]: string } = {
      'idle': 'bg-gray-100 text-gray-600',
      'active': 'bg-green-100 text-green-600',
      'completed': 'bg-blue-100 text-blue-600',
      'error': 'bg-red-100 text-red-600'
    }
    return colors[status] || colors['idle']
  }

  const renderPhaseContent = () => {
    switch (activeTab) {
      case 'spaced-repetition':
        return renderSpacedRepetition()
      case 'active-recall':
        return renderActiveRecall()
      case 'dual-coding':
        return renderDualCoding()
      case 'interleaved-practice':
        return renderInterleavedPractice()
      case 'metacognition':
        return renderMetacognition()
      case 'elaboration-network':
        return renderElaborationNetwork()
      default:
        return null
    }
  }

  const renderSpacedRepetition = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Session Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Cards Studied</span>
                <Badge variant="secondary">{sessionStats.cardsStudied}/{sessionStats.totalCards}</Badge>
              </div>
              <Progress value={(sessionStats.cardsStudied / sessionStats.totalCards) * 100} className="w-full" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Accuracy</span>
                <span className="font-semibold">
                  {sessionStats.cardsStudied > 0
                    ? Math.round((sessionStats.correctAnswers / sessionStats.cardsStudied) * 100)
                    : 0}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Avg Response Time</span>
                <span className="font-semibold">{sessionStats.averageResponseTime}ms</span>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span>Streak: {sessionStats.streakDays} days</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-blue-500" />
                <span>Session time: {Math.floor(sessionStats.sessionDuration / 60)}min</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {currentCard ? (
        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-8">
            <div className="relative h-64 cursor-pointer" onClick={handleCardFlip}>
              <div className={`absolute inset-0 w-full h-full transition-transform duration-500 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
                {/* Front of card */}
                <div className="absolute inset-0 w-full h-full backface-hidden bg-white rounded-lg border border-gray-200 p-6 flex items-center justify-center">
                  <div className="text-center">
                    <h3 className="text-xl font-semibold mb-4">Question:</h3>
                    <p className="text-gray-700">{currentCard.question}</p>
                    <div className="mt-4">
                      <Badge variant="outline">{currentCard.card_type}</Badge>
                      <Badge variant="outline" className="ml-2">
                        Difficulty: {currentCard.difficulty.toFixed(1)}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Back of card */}
                <div className="absolute inset-0 w-full h-full backface-hidden bg-blue-50 rounded-lg border border-blue-200 p-6 flex items-center justify-center rotate-y-180">
                  <div className="text-center">
                    <h3 className="text-xl font-semibold mb-4 text-blue-800">Answer:</h3>
                    <p className="text-blue-700">{currentCard.answer}</p>
                    {currentCard.source_material && (
                      <p className="text-sm text-blue-600 mt-4">
                        Source: {currentCard.source_material}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {showAnswer && (
              <div className="mt-6 space-y-4">
                <div className="flex justify-center gap-2">
                  <span className="text-sm font-medium">Rate your recall:</span>
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <Button
                      key={rating}
                      variant="outline"
                      size="sm"
                      onClick={() => handleQualityRating(rating)}
                      className={rating <= 2 ? 'border-red-200 text-red-600 hover:bg-red-50' :
                                   rating === 3 ? 'border-yellow-200 text-yellow-600 hover:bg-yellow-50' :
                                   'border-green-200 text-green-600 hover:bg-green-50'}
                    >
                      {rating}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {!isFlipped && (
              <div className="mt-6 text-center">
                <Button onClick={handleCardFlip} variant="outline">
                  Show Answer
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">Session Complete!</h3>
            <p className="text-gray-600 mb-4">
              Great job! You've completed all the cards in this session.
            </p>
            <Button onClick={() => window.location.reload()}>Start New Session</Button>
          </CardContent>
        </Card>
      )}
    </div>
  )

  const renderActiveRecall = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Active Recall Practice</CardTitle>
        </CardHeader>
        <CardContent>
          {!currentQuestion ? (
            <div className="text-center py-8">
              <Button onClick={handleStartActiveRecallSession} size="lg">
                <Play className="h-4 w-4 mr-2" />
                Start Practice Session
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">Question:</h3>
                <p className="text-gray-700">{currentQuestion.text}</p>
                <div className="mt-2">
                  <Badge variant="outline">{currentQuestion.type}</Badge>
                  <Badge variant="outline" className="ml-2">{currentQuestion.difficulty}</Badge>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Your Answer:</h3>
                <textarea
                  className="w-full p-3 border rounded-md"
                  rows={3}
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="Type your answer here..."
                />
              </div>

              {currentQuestion.options && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Options:</h3>
                  <div className="space-y-2">
                    {currentQuestion.options.map((option, index) => (
                      <label key={index} className="flex items-center space-x-3 cursor-pointer hover:bg-gray-50 p-2 rounded">
                        <input
                          type="radio"
                          name="answer"
                          value={option}
                          onChange={(e) => setUserAnswer(e.target.value)}
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {feedback && (
                <div className={`p-3 rounded-md ${
                  feedback.includes('completed')
                    ? 'bg-green-50 text-green-700 border-green-200'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}>
                  {feedback}
                </div>
              )}

              <div className="flex gap-2">
                <Button onClick={handleSubmitAnswer} disabled={!userAnswer}>
                  Submit Answer
                </Button>
                <Button variant="outline" onClick={() => setFeedback('')} disabled={!feedback}>
                  Clear
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )

  const renderDualCoding = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Dual Coding Enhancement</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Visual Elements</h3>
              <select
                className="w-full p-2 border rounded-md"
                value={selectedVisualType}
                onChange={(e) => setSelectedVisualType(e.target.value)}
              >
                {visualElements.map((element) => (
                  <option key={element.id} value={element.type}>
                    {element.title}
                  </option>
                ))}
              </select>
            </div>

            <Button onClick={handleCreateDualCoding}>
              Create Visual Enhancement
            </Button>

            {visualElements.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-2">Available Visual Elements</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {visualElements.map((element) => (
                    <Card key={element.id} className="cursor-pointer hover:shadow-md transition-shadow">
                      <CardContent className="p-4 text-center">
                        <div className="text-sm font-medium">{element.title}</div>
                        <div className="text-xs text-gray-500 mt-1">{element.type}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderInterleavedPractice = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Interleaved Practice</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-4">
            Practice multiple concepts together to improve discrimination and retention.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Practice Patterns</h3>
              <Button onClick={() => interleavedPracticeApi.getPracticePatterns()}>
                Load Available Patterns
              </Button>
            </div>

            <Button variant="outline" className="w-full">
              Create Interleaved Schedule
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderMetacognition = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Metacognitive Reflection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Reflection Prompt</h3>
              <div className="p-4 bg-blue-50 rounded-md border border-blue-200">
                <p className="text-blue-700">{reflectionPrompt || 'Loading reflection prompt...'}</p>
              </div>
            </div>

            <Button onClick={handleStartReflection}>
              Start Reflection Activity
            </Button>

            {reflectionResponse && (
              <div>
                <h3 className="text-lg font-semibold mb-2">Your Reflection:</h3>
                <textarea
                  className="w-full p-3 border rounded-md"
                  rows={4}
                  value={reflectionResponse}
                  onChange={(e) => setReflectionResponse(e.target.value)}
                  placeholder="Share your thoughts..."
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderElaborationNetwork = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Knowledge Network</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-gray-600 mb-4">
              Visualize your knowledge connections and identify transfer opportunities.
            </p>

            <Button onClick={handleVisualizeNetwork}>
              Visualize Network
            </Button>

            {networkVisualization && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-2">Network Visualization</h3>
                <div className="h-96 border rounded-md bg-gray-50 flex items-center justify-center">
                  <p className="text-gray-500">Network visualization would be rendered here</p>
                  {/* Replace with actual network visualization component */}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">CLE Practice Session</h1>
        <p className="text-gray-600">Cognitive Learning Engine - Evidence-based practice system</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
          {CLEPhases.map((phase) => (
            <TabsTrigger
              key={phase.id}
              value={phase.id}
              className={`flex items-center gap-2 ${getPhaseColor(phase.status)}`}
            >
              {phase.icon}
              <span className="hidden sm:inline">{phase.name}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {renderPhaseContent()}
        </TabsContent>
      </Tabs>
    </div>
  )
}