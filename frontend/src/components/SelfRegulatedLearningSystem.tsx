'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Brain,
  Target,
  Clock,
  Calendar,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Award,
  BookOpen,
  BarChart3,
  Settings,
  Play,
  Pause,
  RefreshCw,
  Zap,
  Activity,
  Star,
  Flag,
  Lightbulb
} from 'lucide-react'

interface SelfRegulatedLearningSystemProps {
  userId: string
  courseId: string
  onGoalAchieved?: (goal: LearningGoal) => void
}

interface LearningGoal {
  id: string
  title: string
  description: string
  category: 'knowledge' | 'skill' | 'behavior' | 'time'
  targetValue: number
  currentValue: number
  unit: string
  deadline: string
  priority: 'high' | 'medium' | 'low'
  strategies: LearningStrategy[]
  milestones: Milestone[]
  reflectionPrompts: string[]
}

interface LearningStrategy {
  id: string
  name: string
  type: 'cognitive' | 'metacognitive' | 'motivational' | 'resource'
  description: string
  effectiveness: number
  implementation: string
  resources: string[]
}

interface Milestone {
  id: string
  title: string
  targetValue: number
  achieved: boolean
  achievedAt?: string
  reflection?: string
}

interface StudySession {
  id: string
  startTime: string
  endTime?: string
  duration: number
  goals: string[]
  strategies: string[]
  environment: StudyEnvironment
  focusLevel: number
  interruptions: number
  selfEfficacy: number
  reflection: string
}

interface StudyEnvironment {
  location: string
  noiseLevel: number
  distractions: string[]
  tools: string[]
  comfort: number
}

interface SelfReflection {
  id: string
  sessionId?: string
  timestamp: string
  type: 'planning' | 'monitoring' | 'evaluation' | 'strategic'
  questions: ReflectionQuestion[]
  responses: Record<string, string>
  insights: string[]
  actionItems: string[]
}

interface ReflectionQuestion {
  id: string
  question: string
  type: 'rating' | 'text' | 'multiple' | 'checklist'
  options?: string[]
  required: boolean
}

export function SelfRegulatedLearningSystem({
  userId,
  courseId,
  onGoalAchieved
}: SelfRegulatedLearningSystemProps) {
  const [activeGoals, setActiveGoals] = useState<LearningGoal[]>([])
  const [currentSession, setCurrentSession] = useState<StudySession | null>(null)
  const [reflections, setReflections] = useState<SelfReflection[]>([])
  const [availableStrategies, setAvailableStrategies] = useState<LearningStrategy[]>([])
  const [isSessionActive, setIsSessionActive] = useState(false)
  const [currentPhase, setCurrentPhase] = useState<'planning' | 'execution' | 'monitoring' | 'reflection'>('planning')
  const [sessionStats, setSessionStats] = useState({
    totalSessions: 0,
    averageDuration: 0,
    averageFocus: 0,
    completionRate: 0,
    weeklyGoalProgress: 0
  })

  useEffect(() => {
    initializeSelfRegulatedLearning()
  }, [userId, courseId])

  const initializeSelfRegulatedLearning = async () => {
    const goals = await loadLearningGoals()
    const strategies = await loadLearningStrategies()
    const reflections = await loadReflections()
    const stats = await loadSessionStats()

    setActiveGoals(goals)
    setAvailableStrategies(strategies)
    setReflections(reflections)
    setSessionStats(stats)
  }

  const loadLearningGoals = async (): Promise<LearningGoal[]> => {
    return [
      {
        id: 'goal1',
        title: 'Dominare React Hooks Avanzati',
        description: 'Completare tutti i concetti avanzati di React Hooks con confidence ≥ 90%',
        category: 'knowledge',
        targetValue: 90,
        currentValue: 65,
        unit: '%',
        deadline: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
        priority: 'high',
        strategies: [],
        milestones: [
          { id: 'm1', title: 'Comprendere useCallback', targetValue: 80, achieved: true },
          { id: 'm2', title: 'Padroneggiare useReducer', targetValue: 85, achieved: false },
          { id: 'm3', title: 'Implementare custom hooks', targetValue: 90, achieved: false }
        ],
        reflectionPrompts: [
          'Quali hooks trovi più difficili e perché?',
          'Come applicheresti questi concetti in un progetto reale?',
          'Quali risorse aggiuntive ti servono?'
        ]
      },
      {
        id: 'goal2',
        title: 'Studio Consistente',
        description: 'Studiare almeno 5 giorni a settimana per 2 ore',
        category: 'behavior',
        targetValue: 10,
        currentValue: 7,
        unit: 'ore/settimana',
        deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        priority: 'medium',
        strategies: [],
        milestones: [
          { id: 'm4', title: 'Creare routine fissa', targetValue: 5, achieved: true },
          { id: 'm5', title: 'Mantenere streak 7 giorni', targetValue: 7, achieved: false }
        ],
        reflectionPrompts: [
          'Cosa ti ha impedito di studiare regolarmente?',
          'Come puoi ottimizzare il tuo tempo?',
          'Quali sono i tuoi momenti più produttivi?'
        ]
      }
    ]
  }

  const loadLearningStrategies = async (): Promise<LearningStrategy[]> => {
    return [
      {
        id: 's1',
        name: 'Pomodoro Technique',
        type: 'cognitive',
        description: '25 minuti di studio focalizzato con 5 minuti di pausa',
        effectiveness: 0.85,
        implementation: 'Usa un timer per sessioni di 25 minuti con pause strutturate',
        resources: ['Timer', 'Lista di distrazioni da evitare']
      },
      {
        id: 's2',
        name: 'Active Recall',
        type: 'cognitive',
        description: 'Test attivo della memoria senza guardare le note',
        effectiveness: 0.92,
        implementation: 'Dopo aver studiato, chiudi le note e prova a spiegare i concetti',
        resources: ['Flashcards digitali', 'Domande di autovalutazione']
      },
      {
        id: 's3',
        name: 'Metacognitive Monitoring',
        type: 'metacognitive',
        description: 'Monitorare costantemente la propria comprensione',
        effectiveness: 0.78,
        implementation: 'Fai pause regolari per valutare cosa hai capito e cosa no',
        resources: ['Checklist di autovalutazione', 'Journal di apprendimento']
      },
      {
        id: 's4',
        name: 'Goal Setting',
        type: 'motivational',
        description: 'Stabilire obiettivi SMART specifici e misurabili',
        effectiveness: 0.88,
        implementation: 'Definisci obiettivi giornalieri/settimanali specifici',
        resources: ['Template SMART goals', 'Tracker di progressi']
      }
    ]
  }

  const loadReflections = async (): Promise<SelfReflection[]> => {
    return [
      {
        id: 'ref1',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        type: 'evaluation',
        questions: [
          { id: 'q1', question: 'Come valuti la tua comprensione oggi?', type: 'rating', required: true },
          { id: 'q2', question: 'Cosa hai imparato di nuovo?', type: 'text', required: true }
        ],
        responses: { q1: '4', q2: 'Ho capito meglio useReducer' },
        insights: ['Bisogna praticare di più con esempi complessi'],
        actionItems: ['Creare mini-progetti', 'Cercare esempi avanzati']
      }
    ]
  }

  const loadSessionStats = async () => ({
    totalSessions: 12,
    averageDuration: 95,
    averageFocus: 7.5,
    completionRate: 0.83,
    weeklyGoalProgress: 0.7
  })

  const startStudySession = () => {
    const session: StudySession = {
      id: `session_${Date.now()}`,
      startTime: new Date().toISOString(),
      duration: 0,
      goals: activeGoals.filter(g => g.priority === 'high').map(g => g.id),
      strategies: ['s1', 's2'], // Pomodoro + Active Recall
      environment: {
        location: 'Home Office',
        noiseLevel: 2,
        distractions: ['Phone notifications', 'Social media'],
        tools: ['Laptop', 'Headphones', 'Notebook'],
        comfort: 8
      },
      focusLevel: 8,
      interruptions: 0,
      selfEfficacy: 7,
      reflection: ''
    }

    setCurrentSession(session)
    setIsSessionActive(true)
    setCurrentPhase('execution')

    // Start planning reflection
    generatePlanningReflection()
  }

  const generatePlanningReflection = () => {
    const planningReflection: SelfReflection = {
      id: `plan_${Date.now()}`,
      timestamp: new Date().toISOString(),
      type: 'planning',
      questions: [
        { id: 'pq1', question: 'Quali sono i tuoi obiettivi specifici per questa sessione?', type: 'text', required: true },
        { id: 'pq2', question: 'Quanto ti senti motivato (1-10)?', type: 'rating', required: true },
        { id: 'pq3', question: 'Quali strategie userai?', type: 'checklist', options: ['Pomodoro', 'Active Recall', 'Note Taking'], required: true },
        { id: 'pq4', question: 'Quali potenziali distrazioni prevedi?', type: 'text', required: false }
      ],
      responses: {},
      insights: [],
      actionItems: []
    }

    setReflections(prev => [...prev, planningReflection])
  }

  const pauseSession = () => {
    if (!currentSession) return

    const updatedSession = {
      ...currentSession,
      endTime: new Date().toISOString(),
      duration: Math.floor((Date.now() - new Date(currentSession.startTime).getTime()) / 1000 / 60)
    }

    setCurrentSession(updatedSession)
    setIsSessionActive(false)
    setCurrentPhase('monitoring')

    // Generate monitoring reflection
    generateMonitoringReflection(updatedSession)
  }

  const generateMonitoringReflection = (session: StudySession) => {
    const monitoringReflection: SelfReflection = {
      id: `mon_${Date.now()}`,
      sessionId: session.id,
      timestamp: new Date().toISOString(),
      type: 'monitoring',
      questions: [
        { id: 'mq1', question: 'Sei riuscito a mantenere il focus?', type: 'rating', required: true },
        { id: 'mq2', question: 'Hai incontrato difficoltà inaspettate?', type: 'text', required: true },
        { id: 'mq3', question: 'Le strategie sono state efficaci?', type: 'rating', required: true }
      ],
      responses: {},
      insights: [],
      actionItems: []
    }

    setReflections(prev => [...prev, monitoringReflection])
  }

  const completeSession = (reflectionResponses: Record<string, string>) => {
    if (!currentSession) return

    const completedSession = {
      ...currentSession,
      endTime: new Date().toISOString(),
      duration: Math.floor((Date.now() - new Date(currentSession.startTime).getTime()) / 1000 / 60),
      reflection: Object.values(reflectionResponses).join(' | ')
    }

    // Update session stats
    setSessionStats(prev => ({
      totalSessions: prev.totalSessions + 1,
      averageDuration: (prev.averageDuration * prev.totalSessions + completedSession.duration) / (prev.totalSessions + 1),
      averageFocus: (prev.averageFocus * prev.totalSessions + completedSession.focusLevel) / (prev.totalSessions + 1),
      completionRate: prev.completionRate * 0.9 + 0.1, // Incremental improvement
      weeklyGoalProgress: Math.min(1, prev.weeklyGoalProgress + 0.1)
    }))

    // Update goals progress
    updateGoalsProgress(completedSession)

    setCurrentSession(null)
    setIsSessionActive(false)
    setCurrentPhase('reflection')

    // Generate evaluation reflection
    generateEvaluationReflection(completedSession)
  }

  const updateGoalsProgress = (session: StudySession) => {
    setActiveGoals(prev => prev.map(goal => {
      if (session.goals.includes(goal.id)) {
        const progressIncrease = session.duration > 60 ? 5 : 2
        const newValue = Math.min(goal.targetValue, goal.currentValue + progressIncrease)

        return {
          ...goal,
          currentValue: newValue
        }
      }
      return goal
    }))
  }

  const generateEvaluationReflection = (session: StudySession) => {
    const evaluationReflection: SelfReflection = {
      id: `eval_${Date.now()}`,
      sessionId: session.id,
      timestamp: new Date().toISOString(),
      type: 'evaluation',
      questions: [
        { id: 'eq1', question: 'Cosa hai imparato in questa sessione?', type: 'text', required: true },
        { id: 'eq2', question: 'Cosa funzionato bene?', type: 'text', required: true },
        { id: 'eq3', question: 'Cosa miglioreresti nella prossima sessione?', type: 'text', required: true },
        { id: 'eq4', question: 'Quanto ti senti più sicuro ora (1-10)?', type: 'rating', required: true }
      ],
      responses: {},
      insights: [
        'Sessione produttiva, focus mantenuto bene',
        'Le strategie usate sono state efficaci'
      ],
      actionItems: [
        'Continuare con la stessa routine',
        'Provare esempi più complessi la prossima volta'
      ]
    }

    setReflections(prev => [...prev, evaluationReflection])
  }

  const getRecommendedStrategies = () => {
    // Analyze performance and recommend strategies
    if (sessionStats.averageFocus < 6) {
      return availableStrategies.filter(s => s.type === 'cognitive').slice(0, 2)
    }
    if (sessionStats.completionRate < 0.7) {
      return availableStrategies.filter(s => s.type === 'motivational').slice(0, 2)
    }
    return availableStrategies.slice(0, 3)
  }

  const getWeeklyOverview = () => {
    const now = new Date()
    const weekStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay())
    const weekEnd = new Date(weekStart.getTime() + 7 * 24 * 60 * 60 * 1000)

    const weeklyGoals = activeGoals.filter(g =>
      new Date(g.deadline) <= weekEnd && new Date(g.deadline) >= weekStart
    )

    return {
      totalGoals: weeklyGoals.length,
      completedGoals: weeklyGoals.filter(g => g.currentValue >= g.targetValue * 0.8).length,
      inProgressGoals: weeklyGoals.filter(g => g.currentValue > 0 && g.currentValue < g.targetValue * 0.8).length,
      notStartedGoals: weeklyGoals.filter(g => g.currentValue === 0).length
    }
  }

  const weeklyOverview = getWeeklyOverview()
  const recommendedStrategies = getRecommendedStrategies()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-green-500 to-blue-600 rounded-xl">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Sistema di Auto-Regolazione dell'Apprendimento
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Pianificazione → Esecuzione → Monitoraggio → Riflessione
              </p>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-lg font-medium ${
            currentPhase === 'planning' ? 'bg-blue-100 text-blue-800' :
            currentPhase === 'execution' ? 'bg-green-100 text-green-800' :
            currentPhase === 'monitoring' ? 'bg-yellow-100 text-yellow-800' :
            'bg-purple-100 text-purple-800'
          }`}>
            {currentPhase === 'planning' ? 'Pianificazione' :
             currentPhase === 'execution' ? 'Esecuzione' :
             currentPhase === 'monitoring' ? 'Monitoraggio' : 'Riflessione'}
          </div>
        </div>

        {/* Self-Regulation Cycle */}
        <div className="flex items-center justify-between mb-4">
          {[
            { phase: 'planning', icon: Target, label: 'Pianifica' },
            { phase: 'execution', icon: Play, label: 'Esegui' },
            { phase: 'monitoring', icon: Activity, label: 'Monitora' },
            { phase: 'reflection', icon: Brain, label: 'Rifletti' }
          ].map((item, index) => (
            <div key={item.phase} className="flex items-center space-x-2">
              <div className={`p-2 rounded-lg ${
                currentPhase === item.phase ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'
              }`}>
                <item.icon className="h-4 w-4" />
              </div>
              <span className={`text-sm font-medium ${
                currentPhase === item.phase ? 'text-blue-600' : 'text-gray-400'
              }`}>
                {item.label}
              </span>
              {index < 3 && <div className="w-8 h-0.5 bg-gray-300" />}
            </div>
          ))}
        </div>
      </div>

      {/* Weekly Overview */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-4">
          <Calendar className="h-5 w-5 text-blue-600" />
          <h4 className="font-semibold text-gray-900">Panoramica Settimanale</h4>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{weeklyOverview.totalGoals}</div>
            <p className="text-xs text-gray-600">Obiettivi Totali</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{weeklyOverview.completedGoals}</div>
            <p className="text-xs text-gray-600">Completati</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{weeklyOverview.inProgressGoals}</div>
            <p className="text-xs text-gray-600">In Corso</p>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{weeklyOverview.notStartedGoals}</div>
            <p className="text-xs text-gray-600">Da Iniziare</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${(weeklyOverview.completedGoals / Math.max(weeklyOverview.totalGoals, 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Active Goals */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Flag className="h-5 w-5 text-purple-600" />
            <h4 className="font-semibold text-gray-900">Obiettivi Attivi</h4>
          </div>
          <button className="btn btn-primary btn-sm">
            <Target className="h-4 w-4 mr-2" />
            Nuovo Obiettivo
          </button>
        </div>

        <div className="space-y-4">
          {activeGoals.map((goal) => (
            <div key={goal.id} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex-1">
                  <h5 className="font-medium text-gray-900">{goal.title}</h5>
                  <p className="text-sm text-gray-600 mt-1">{goal.description}</p>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  goal.priority === 'high' ? 'bg-red-100 text-red-800' :
                  goal.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {goal.priority}
                </div>
              </div>

              {/* Progress */}
              <div className="mb-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">Progresso</span>
                  <span className="text-sm font-medium text-gray-900">
                    {Math.round((goal.currentValue / goal.targetValue) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, (goal.currentValue / goal.targetValue) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Details */}
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>{goal.currentValue}/{goal.targetValue} {goal.unit}</span>
                <span>Scadenza: {new Date(goal.deadline).toLocaleDateString()}</span>
              </div>

              {/* Milestones */}
              {goal.milestones.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-sm font-medium text-gray-700 mb-2">Milestones</div>
                  <div className="flex space-x-2">
                    {goal.milestones.map((milestone) => (
                      <div
                        key={milestone.id}
                        className={`flex items-center space-x-1 px-2 py-1 rounded text-xs ${
                          milestone.achieved
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {milestone.achieved ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <div className="w-3 h-3 border border-gray-400 rounded-full" />
                        )}
                        <span>{milestone.title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Current Session Controls */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900">Sessione di Studio</h4>
          {currentSession && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>
                {Math.floor((Date.now() - new Date(currentSession.startTime).getTime()) / 1000 / 60)} min
              </span>
            </div>
          )}
        </div>

        {!isSessionActive ? (
          <button
            onClick={startStudySession}
            className="w-full btn btn-primary"
          >
            <Play className="h-5 w-5 mr-2" />
            Inizia Sessione di Studio
          </button>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-800 font-medium">Sessione in corso</span>
              </div>
              <button
                onClick={pauseSession}
                className="btn btn-secondary btn-sm"
              >
                <Pause className="h-4 w-4 mr-2" />
                Pausa
              </button>
            </div>

            {currentSession && (
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-bold text-gray-900">{currentSession.focusLevel}/10</div>
                  <p className="text-xs text-gray-600">Focus</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-bold text-gray-900">{currentSession.interruptions}</div>
                  <p className="text-xs text-gray-600">Interruzioni</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-bold text-gray-900">{currentSession.selfEfficacy}/10</div>
                  <p className="text-xs text-gray-600">Auto-efficacia</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Recommended Strategies */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center space-x-3 mb-4">
          <Lightbulb className="h-5 w-5 text-yellow-600" />
          <h4 className="font-semibold text-gray-900">Strategie Raccomandate</h4>
        </div>

        <div className="space-y-3">
          {recommendedStrategies.map((strategy) => (
            <div key={strategy.id} className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h5 className="font-medium text-gray-900">{strategy.name}</h5>
                  <p className="text-sm text-gray-600 mt-1">{strategy.description}</p>
                  <div className="mt-2 flex items-center space-x-2">
                    <span className="text-xs text-gray-500">Efficacia:</span>
                    <div className="flex items-center space-x-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-3 w-3 ${
                            i < Math.round(strategy.effectiveness * 5)
                              ? 'text-yellow-500 fill-current'
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  strategy.type === 'cognitive' ? 'bg-blue-100 text-blue-800' :
                  strategy.type === 'metacognitive' ? 'bg-purple-100 text-purple-800' :
                  strategy.type === 'motivational' ? 'bg-green-100 text-green-800' :
                  'bg-orange-100 text-orange-800'
                }`}>
                  {strategy.type}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Reflections */}
      {reflections.length > 0 && (
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <div className="flex items-center space-x-3 mb-4">
            <Brain className="h-5 w-5 text-purple-600" />
            <h4 className="font-semibold text-gray-900">Riflessioni Recenti</h4>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto">
            {reflections.slice(-5).reverse().map((reflection) => (
              <div key={reflection.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    reflection.type === 'planning' ? 'bg-blue-100 text-blue-800' :
                    reflection.type === 'strategic' ? 'bg-green-100 text-green-800' :
                    reflection.type === 'monitoring' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {reflection.type === 'planning' ? 'Pianificazione' :
                     reflection.type === 'strategic' ? 'Strategico' :
                     reflection.type === 'monitoring' ? 'Monitoraggio' : 'Valutazione'}
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(reflection.timestamp).toLocaleString()}
                  </span>
                </div>

                {reflection.insights.length > 0 && (
                  <div className="mb-2">
                    <div className="text-sm font-medium text-gray-700 mb-1">Insights:</div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {reflection.insights.map((insight, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-purple-500 mr-2">•</span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {reflection.actionItems.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-1">Azioni da intraprendere:</div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {reflection.actionItems.map((action, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-green-500 mr-2">•</span>
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}