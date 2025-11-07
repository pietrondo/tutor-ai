'use client'

import { useState, useEffect } from 'react'
import { Clock, Target, Flame, BookOpen } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

interface StudyProgressProps {
  courseId: string
}

interface ProgressData {
  course_id: string
  total_sessions: number
  total_study_time: number
  topics_covered: string[]
  last_study_date: string | null
  streak_days: number
  weekly_goal: number
  weekly_progress: number
}

interface StudyInsights {
  total_sessions: number
  total_study_hours: number
  average_session_minutes: number
  most_common_topics: Array<{ topic: string; count: number }>
  study_pattern_by_day: Record<string, number>
  last_study_date: string
}

export function StudyProgress({ courseId }: StudyProgressProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null)
  const [insights, setInsights] = useState<StudyInsights | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProgress()
  }, [courseId])

  const fetchProgress = async () => {
    try {
      const [progressResponse, insightsResponse] = await Promise.all([
        fetch(`http://localhost:8000/study-progress/${courseId}`),
        fetch(`http://localhost:8000/study-insights/${courseId}`)
      ])

      const progressData = await progressResponse.json()
      const insightsData = await insightsResponse.json()

      setProgress(progressData.progress)
      setInsights(insightsData)
    } catch (error) {
      console.error('Errore nel caricamento dei progressi:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatStudyTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h ${mins}m`
    }
    return `${mins}m`
  }

  const getWeeklyProgressData = () => {
    if (!progress) return []

    const days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    const currentDay = new Date().getDay()
    const adjustedDay = currentDay === 0 ? 6 : currentDay - 1

    return days.map((day, index) => ({
      day,
      hours: index <= adjustedDay ? (progress.weekly_progress / 7) : 0,
      goal: progress.weekly_goal / 7
    }))
  }

  const getStudyPatternData = () => {
    if (!insights?.study_pattern_by_day) return []

    const dayOrder = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

    return dayOrder.map(day => ({
      day: day.slice(0, 3),
      sessions: insights.study_pattern_by_day[day] || 0
    }))
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!progress || !insights) {
    return (
      <div className="text-center py-12 text-gray-500">
        Nessun dato di progressi disponibile
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Sessioni Totali</p>
              <p className="text-2xl font-bold text-gray-900">{progress.total_sessions}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <BookOpen className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tempo Totale</p>
              <p className="text-2xl font-bold text-gray-900">{formatStudyTime(progress.total_study_time)}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Clock className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Serie Giornaliera</p>
              <p className="text-2xl font-bold text-gray-900">{progress.streak_days} giorni</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <Flame className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Argomenti Coperti</p>
              <p className="text-2xl font-bold text-gray-900">{(progress.topics_covered || []).length}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Target className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Weekly Progress */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Progresso Settimanale</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={getWeeklyProgressData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}h`, '']} />
              <Bar dataKey="hours" fill="#3B82F6" name="Ore studiate" />
              <Bar dataKey="goal" fill="#E5E7EB" name="Obiettivo giornaliero" />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-gray-600 text-center">
            Obiettivo settimanale: {progress.weekly_goal}h | Completato: {progress.weekly_progress.toFixed(1)}h
          </div>
        </div>

        {/* Study Pattern */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Pattern di Studio</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={getStudyPatternData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="sessions" stroke="#8B5CF6" strokeWidth={2} name="Sessioni" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Topics and Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Most Studied Topics */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Argomenti più Studiati</h3>
          {(insights?.most_common_topics ?? []).length > 0 ? (
            <div className="space-y-3">
              {(insights?.most_common_topics ?? []).map((topic, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 capitalize">{topic.topic}</span>
                  <span className="text-sm text-gray-500">{topic.count} volte</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Nessun argomento tracciato ancora</p>
          )}
        </div>

        {/* Study Statistics */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Statistiche di Studio</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Durata media sessione</span>
              <span className="text-sm font-medium text-gray-900">
                {insights.average_session_minutes} minuti
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Ultimo studio</span>
              <span className="text-sm font-medium text-gray-900">
                {progress.last_study_date
                  ? new Date(progress.last_study_date).toLocaleDateString('it-IT')
                  : 'Mai'
                }
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Media ore/settimana</span>
              <span className="text-sm font-medium text-gray-900">
                {(insights.total_study_hours / Math.max(1, progress.total_sessions / 7)).toFixed(1)}h
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* All Topics */}
      {((progress.topics_covered ?? [])).length > 0 && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Tutti gli Argomenti Coperti</h3>
          <div className="flex flex-wrap gap-2">
            {(progress.topics_covered ?? []).map((topic, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
