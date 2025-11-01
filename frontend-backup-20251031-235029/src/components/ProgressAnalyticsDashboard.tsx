'use client'

import { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  Clock,
  Award,
  BookOpen,
  BarChart3,
  Calendar,
  Activity,
  Zap,
  CheckCircle,
  AlertCircle,
  Users,
  FileText
} from 'lucide-react'
import { UserProgress, Concept, ConceptMasteryVerification } from '@/types/indexing'

interface ProgressAnalyticsDashboardProps {
  userId: string
  courseId: string
  timeRange?: '7d' | '30d' | '90d' | 'all'
}

interface AnalyticsData {
  userProgress: UserProgress
  concepts: Concept[]
  recentVerifications: ConceptMasteryVerification[]
  learningStreak: {
    current: number
    longest: number
    lastStudyDate: string
  }
  performanceMetrics: {
    averageScore: number
    improvementRate: number
    totalStudyTime: number
    conceptsMastered: number
    conceptsInProgress: number
    conceptsToReview: number
  }
  weeklyActivity: {
    week: string
    studyMinutes: number
    testsTaken: number
    averageScore: number
  }[]
  subjectProgress: {
    category: string
    mastery: number
    timeSpent: number
    conceptsCount: number
    trend: 'up' | 'down' | 'stable'
  }[]
}

export function ProgressAnalyticsDashboard({
  userId,
  courseId,
  timeRange = '30d'
}: ProgressAnalyticsDashboardProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedView, setSelectedView] = useState<'overview' | 'concepts' | 'activity' | 'trends'>('overview')

  useEffect(() => {
    loadAnalyticsData()
  }, [userId, courseId, timeRange])

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch(
        `/api/users/${userId}/analytics?courseId=${courseId}&timeRange=${timeRange}`
      )
      if (!response.ok) {
        throw new Error('Failed to load analytics data')
      }

      const data = await response.json()
      setAnalyticsData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
      console.error('Error loading analytics:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />
      default:
        return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
    if (level >= 0.6) return 'text-blue-600 bg-blue-50 border-blue-200'
    if (level >= 0.4) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const renderOverview = () => {
    if (!analyticsData) return null

    const { userProgress, performanceMetrics, learningStreak } = analyticsData

    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Brain className="h-5 w-5 text-purple-600" />
              <span className="text-sm text-green-600 font-medium">
                +{performanceMetrics.improvementRate.toFixed(1)}%
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {performanceMetrics.averageScore.toFixed(0)}%
            </div>
            <p className="text-xs text-gray-500">Punteggio Medio</p>
          </div>

          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <span className="text-sm text-gray-600">questa settimana</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(performanceMetrics.totalStudyTime / 60)}h
            </div>
            <p className="text-xs text-gray-500">Tempo di Studio</p>
          </div>

          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Target className="h-5 w-5 text-green-600" />
              <span className="text-sm text-gray-600">totali</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {performanceMetrics.conceptsMastered}
            </div>
            <p className="text-xs text-gray-500">Concetti Dominati</p>
          </div>

          <div className="glass rounded-xl p-4 border border-gray-200/50">
            <div className="flex items-center justify-between mb-2">
              <Activity className="h-5 w-5 text-orange-600" />
              <span className="text-sm text-orange-600 font-medium">
                {learningStreak.current} giorni
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {learningStreak.current}
            </div>
            <p className="text-xs text-gray-500">Serie di Studio</p>
          </div>
        </div>

        {/* Progress Overview */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Progresso Complessivo</h4>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Completamento Corso</span>
                <span className="text-sm text-gray-600">
                  {performanceMetrics.conceptsMastered} / {performanceMetrics.conceptsMastered + performanceMetrics.conceptsInProgress + performanceMetrics.conceptsToReview}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-green-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                  style={{
                    width: `${(performanceMetrics.conceptsMastered / (performanceMetrics.conceptsMastered + performanceMetrics.conceptsInProgress + performanceMetrics.conceptsToReview)) * 100}%`
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-green-600">
                  {performanceMetrics.conceptsMastered}
                </div>
                <p className="text-xs text-gray-500">Dominati</p>
              </div>
              <div>
                <div className="text-lg font-bold text-blue-600">
                  {performanceMetrics.conceptsInProgress}
                </div>
                <p className="text-xs text-gray-500">In Corso</p>
              </div>
              <div>
                <div className="text-lg font-bold text-orange-600">
                  {performanceMetrics.conceptsToReview}
                </div>
                <p className="text-xs text-gray-500">Da Rivedere</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Attività Recente</h4>
          <div className="space-y-3">
            {analyticsData.recentVerifications.slice(0, 5).map((verification) => (
              <div key={verification.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${getMasteryColor(verification.mastery_level)}`}>
                    <Brain className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">
                      Concetto {verification.concept_id.slice(0, 8)}...
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(verification.verified_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">
                    {Math.round(verification.mastery_level * 100)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {verification.score.toFixed(0)} pts
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderConceptsView = () => {
    if (!analyticsData) return null

    const { concepts, subjectProgress } = analyticsData

    return (
      <div className="space-y-6">
        {/* Subject Breakdown */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Progresso per Categoria</h4>
          <div className="space-y-4">
            {subjectProgress.map((subject) => (
              <div key={subject.category} className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <BookOpen className="h-5 w-5 text-blue-600" />
                    <div>
                      <div className="font-medium text-gray-900">{subject.category}</div>
                      <div className="text-sm text-gray-500">
                        {subject.conceptsCount} concetti • {Math.round(subject.timeSpent / 60)}h
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getTrendIcon(subject.trend)}
                    <span className={`badge ${getMasteryColor(subject.mastery)}`}>
                      {Math.round(subject.mastery * 100)}%
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      subject.mastery >= 0.8 ? 'bg-green-500' :
                      subject.mastery >= 0.6 ? 'bg-blue-500' :
                      subject.mastery >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${subject.mastery * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Concept Details */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Dettagli Concetti</h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {concepts.map((concept) => (
              <div
                key={concept.id}
                className={`p-4 rounded-xl border transition-all duration-200 ${
                  concept.mastery_level >= 0.8
                    ? 'border-green-200 bg-green-50'
                    : concept.mastery_level >= 0.6
                    ? 'border-blue-200 bg-blue-50'
                    : concept.mastery_level >= 0.4
                    ? 'border-yellow-200 bg-yellow-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${getMasteryColor(concept.mastery_level || 0)}`}>
                      <Brain className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{concept.name}</div>
                      <div className="text-sm text-gray-500">
                        {concept.category} • Difficoltà: {concept.difficulty}/5
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {concept.mastery_level && (
                      <span className={`badge ${getMasteryColor(concept.mastery_level)}`}>
                        {Math.round(concept.mastery_level * 100)}%
                      </span>
                    )}
                    {concept.last_reviewed && (
                      <span className="text-xs text-gray-500">
                        {new Date(concept.last_reviewed).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderActivityView = () => {
    if (!analyticsData) return null

    const { weeklyActivity, performanceMetrics } = analyticsData

    return (
      <div className="space-y-6">
        {/* Weekly Activity Chart */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Attività Settimanale</h4>
          <div className="space-y-4">
            {weeklyActivity.map((week) => (
              <div key={week.week} className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-medium text-gray-900">{week.week}</div>
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4 text-blue-600" />
                      <span>{Math.round(week.studyMinutes / 60)}h</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <FileText className="h-4 w-4 text-purple-600" />
                      <span>{week.testsTaken} test</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Target className="h-4 w-4 text-green-600" />
                      <span>{week.averageScore.toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Tempo</div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${Math.min(100, (week.studyMinutes / 300) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Test</div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-500 h-2 rounded-full"
                        style={{ width: `${Math.min(100, (week.testsTaken / 10) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Punteggio</div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${week.averageScore}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Learning Patterns */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Pattern di Apprendimento</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
              <div className="flex items-center space-x-3 mb-2">
                <Clock className="h-5 w-5 text-blue-600" />
                <span className="font-medium text-blue-900">Momento Attivo</span>
              </div>
              <p className="text-sm text-blue-700">
                Sei più attivo tra le 14:00 e le 18:00, con una performance media del {Math.round(performanceMetrics.averageScore * 1.1)}%
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center space-x-3 mb-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span className="font-medium text-green-900">Tendenza Positiva</span>
              </div>
              <p className="text-sm text-green-700">
                La tua performance è migliorata del {performanceMetrics.improvementRate.toFixed(1)}% nell'ultimo mese
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
              <div className="flex items-center space-x-3 mb-2">
                <Zap className="h-5 w-5 text-purple-600" />
                <span className="font-medium text-purple-900">Efficienza</span>
              </div>
              <p className="text-sm text-purple-700">
                Impieghi in media {Math.round(performanceMetrics.totalStudyTime / performanceMetrics.conceptsMastered)} minuti per concetto
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-xl border border-orange-200">
              <div className="flex items-center space-x-3 mb-2">
                <Award className="h-5 w-5 text-orange-600" />
                <span className="font-medium text-orange-900">Obiettivi</span>
              </div>
              <p className="text-sm text-orange-700">
                Hai completato {performanceMetrics.conceptsMastered} concetti questo mese
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderTrendsView = () => {
    if (!analyticsData) return null

    return (
      <div className="space-y-6">
        {/* Performance Trends */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Tendenze di Performance</h4>
          <div className="space-y-4">
            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-green-900">Punteggio Medio</span>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="h-4 w-4 text-green-600" />
                  <span className="text-green-600">+{analyticsData.performanceMetrics.improvementRate.toFixed(1)}%</span>
                </div>
              </div>
              <div className="text-sm text-green-700">
                In miglioramento costante nelle ultime settimane
              </div>
            </div>

            <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-blue-900">Tempo di Studio</span>
                <div className="flex items-center space-x-1">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span className="text-blue-600">Stabile</span>
                </div>
              </div>
              <div className="text-sm text-blue-700">
                {Math.round(analyticsData.performanceMetrics.totalStudyTime / 60)} ore totali questo mese
              </div>
            </div>

            <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-purple-900">Velocità di Apprendimento</span>
                <div className="flex items-center space-x-1">
                  <Zap className="h-4 w-4 text-purple-600" />
                  <span className="text-purple-600">Alta</span>
                </div>
              </div>
              <div className="text-sm text-purple-700">
                Stai dominando {analyticsData.performanceMetrics.conceptsMastered} concetti al mese
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div className="glass rounded-2xl p-6 border border-gray-200/50">
          <h4 className="font-semibold text-gray-900 mb-4">Raccomandazioni Personalizzate</h4>
          <div className="space-y-3">
            <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <div className="font-medium text-blue-900">Fissa sessioni di studio più brevi</div>
                <div className="text-sm text-blue-700">
                  La tua performance migliora con sessioni sotto i 45 minuti
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <div className="font-medium text-green-900">Continua con la routine attuale</div>
                <div className="text-sm text-green-700">
                  La tua costanza sta dando ottimi risultati
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3 p-3 bg-purple-50 rounded-lg">
              <Target className="h-5 w-5 text-purple-600 mt-0.5" />
              <div>
                <div className="font-medium text-purple-900">Focalizzati sui concetti deboli</div>
                <div className="text-sm text-purple-700">
                  Ci sono {analyticsData.performanceMetrics.conceptsToReview} concetti che necessitano revisione
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="glass rounded-2xl p-8 border border-gray-200/50 text-center">
        <BarChart3 className="h-8 w-8 text-blue-600 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Caricamento analisi delle performance...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass rounded-2xl p-8 border border-gray-200/50 text-center">
        <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadAnalyticsData}
          className="btn btn-primary btn-sm mt-4"
        >
          Riprova
        </button>
      </div>
    )
  }

  if (!analyticsData) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass rounded-2xl p-6 border border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">
                Dashboard Analytics
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Analisi dettagliata del tuo progresso di apprendimento
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={timeRange}
              onChange={(e) => setSelectedView(e.target.value as any)}
              className="form-input text-sm"
            >
              <option value="7d">Ultimi 7 giorni</option>
              <option value="30d">Ultimi 30 giorni</option>
              <option value="90d">Ultimi 90 giorni</option>
              <option value="all">Sempre</option>
            </select>
          </div>
        </div>

        {/* View Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {[
            { id: 'overview', label: 'Panoramica', icon: BarChart3 },
            { id: 'concepts', label: 'Concetti', icon: Brain },
            { id: 'activity', label: 'Attività', icon: Activity },
            { id: 'trends', label: 'Tendenze', icon: TrendingUp }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedView(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ${
                selectedView === tab.id
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Based on Selected View */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'concepts' && renderConceptsView()}
      {selectedView === 'activity' && renderActivityView()}
      {selectedView === 'trends' && renderTrendsView()}
    </div>
  )
}