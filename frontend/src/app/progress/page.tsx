'use client'

import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, Clock, BookOpen, Target, Award, Calendar, Brain } from 'lucide-react'

interface WeeklyProgress {
  day: string
  minutes: number
  sessions: number
}

interface WeeklyProgressApi {
  day: string
  minutes?: number
  sessions?: number
  date?: string
}

interface Achievement {
  title: string
  description: string
  icon: string
  date: string
}

interface ProgressData {
  totalStudyTime: number
  sessionsCompleted: number
  coursesInProgress: number
  conceptsLearned: number
  weeklyProgress: WeeklyProgress[]
  recentAchievements: Achievement[]
}

export default function ProgressPage() {
  const [progressData, setProgressData] = useState<ProgressData>({
    totalStudyTime: 0,
    sessionsCompleted: 0,
    coursesInProgress: 0,
    conceptsLearned: 0,
    weeklyProgress: [],
    recentAchievements: []
  })

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProgressData()
  }, [])

  const fetchProgressData = async () => {
    try {
      console.log('Fetching progress data...')
      const response = await fetch('http://localhost:8000/study-progress/overview')
      console.log('Response status:', response.status)

      if (!response.ok) {
        throw new Error(`Failed to fetch progress data: ${response.status}`)
      }

      const data = await response.json()
      console.log('API Response:', data)

      // The API returns data wrapped in a "progress" object
      const progressData = data.progress || data
      console.log('Progress data:', progressData)

      // Map Italian day names
      const dayNames: { [key: string]: string } = {
        'Mon': 'Lun',
        'Tue': 'Mar',
        'Wed': 'Mer',
        'Thu': 'Gio',
        'Fri': 'Ven',
        'Sat': 'Sab',
        'Sun': 'Dom'
      }

      // Generate achievements based on real data
      const achievements: Achievement[] = []
      if (progressData.total_sessions >= 7) {
        achievements.push({
          title: 'Settimana Produttiva',
          description: `Hai completato ${progressData.total_sessions} sessioni di studio`,
          icon: '🔥',
          date: new Date().toISOString().split('T')[0]
        })
      }
      if (progressData.total_study_time >= 120) {
        achievements.push({
          title: 'Maratona di Studio',
          description: `Oltre ${Math.round(progressData.total_study_time / 60)} ore di studio totale`,
          icon: '⚡',
          date: new Date().toISOString().split('T')[0]
        })
      }
      const conceptsLearned = progressData.total_concepts_learned || 0
      if (conceptsLearned >= 10) {
        achievements.push({
          title: 'Esploratore di Concetti',
          description: `Hai appreso ${conceptsLearned} nuovi concetti`,
          icon: '🎯',
          date: new Date().toISOString().split('T')[0]
        })
      }

      // Ensure weekly_progress is an array before mapping
      let weeklyProgressData: WeeklyProgressApi[] = Array.isArray(progressData.weekly_progress)
        ? progressData.weekly_progress
        : []

      // If weekly_progress is empty, generate default data for the week
      if (weeklyProgressData.length === 0) {
        const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weeklyProgressData = dayNames.map(day => ({
          day: day,
          date: new Date().toISOString().split('T')[0],
          minutes: 0,
          sessions: 0
        }))
      }

      const newData: ProgressData = {
        totalStudyTime: progressData.total_study_time || 0,
        sessionsCompleted: progressData.total_sessions || 0,
        coursesInProgress: progressData.courses_with_progress || 0,
        conceptsLearned: conceptsLearned,
        weeklyProgress: weeklyProgressData.map((day) => ({
          day: dayNames[day.day] || day.day,
          minutes: day.minutes || 0,
          sessions: day.sessions || 0
        })),
        recentAchievements: achievements
      }

      console.log('Setting progress data:', newData)
      setProgressData(newData)
    } catch (error) {
      console.error('Errore nel caricamento dei dati di progresso:', error)
      // Set default empty state on error
      setProgressData({
        totalStudyTime: 0,
        sessionsCompleted: 0,
        coursesInProgress: 0,
        conceptsLearned: 0,
        weeklyProgress: [],
        recentAchievements: []
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-t-purple-600 rounded-full animate-spin mx-auto" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
          </div>
          <p className="mt-4 text-gray-600 font-medium animate-pulse">Caricamento progressi...</p>
        </div>
      </div>
    )
  }

  const maxMinutes = Array.isArray(progressData.weeklyProgress) && progressData.weeklyProgress.length > 0
    ? Math.max(...progressData.weeklyProgress.map(day => day.minutes))
    : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container-responsive py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-2">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
              <BarChart3 className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">I Tuoi Progressi</h1>
              <p className="text-gray-600 mt-1">Traccia il tuo percorso di apprendimento</p>
            </div>
          </div>
        </div>

        {/* Main Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="glass-card p-6">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Clock className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Tempo Totale</p>
                <p className="text-2xl font-bold text-gray-900">{Math.round(progressData.totalStudyTime / 60)}h</p>
                <p className="text-xs text-gray-500">{progressData.totalStudyTime} minuti</p>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <Target className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Sessioni</p>
                <p className="text-2xl font-bold text-gray-900">{progressData.sessionsCompleted}</p>
                <p className="text-xs text-gray-500">Completate</p>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-purple-100 rounded-lg">
                <BookOpen className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Corsi Attivi</p>
                <p className="text-2xl font-bold text-gray-900">{progressData.coursesInProgress}</p>
                <p className="text-xs text-gray-500">In corso</p>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Brain className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Concetti</p>
                <p className="text-2xl font-bold text-gray-900">{progressData.conceptsLearned}</p>
                <p className="text-xs text-gray-500">Imparati</p>
              </div>
            </div>
          </div>
        </div>

        {/* Weekly Progress Chart */}
        <div className="glass-card p-6 mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Calendar className="h-5 w-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Progresso Settimanale</h3>
          </div>

          <div className="space-y-4">
            {Array.isArray(progressData.weeklyProgress) && progressData.weeklyProgress.map((day) => (
              <div key={day.day} className="flex items-center space-x-4">
                <div className="w-12 text-sm font-medium text-gray-700">{day.day}</div>
                <div className="flex-1 relative">
                  <div className="w-full bg-gray-200 rounded-full h-8">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-600 h-8 rounded-full flex items-center justify-end pr-3 transition-all duration-500"
                      style={{ width: `${(day.minutes / maxMinutes) * 100}%` }}
                    >
                      <span className="text-xs font-medium text-white">
                        {day.minutes}min
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  {day.sessions} {day.sessions === 1 ? 'sessione' : 'sessioni'}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Totale settimanale</span>
              <span className="text-lg font-semibold text-gray-900">
                {Array.isArray(progressData.weeklyProgress) ? progressData.weeklyProgress.reduce((sum, day) => sum + day.minutes, 0) : 0} minuti
              </span>
            </div>
          </div>
        </div>

        {/* Recent Achievements */}
        <div className="glass-card p-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Award className="h-5 w-5 text-yellow-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Obiettivi Raggiunti</h3>
          </div>

          <div className="space-y-4">
            {Array.isArray(progressData.recentAchievements) && progressData.recentAchievements.map((achievement, index) => (
              <div key={index} className="flex items-start space-x-4 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg border border-yellow-200">
                <div className="text-2xl">{achievement.icon}</div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{achievement.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{achievement.description}</p>
                  <p className="text-xs text-gray-500 mt-2">{achievement.date}</p>
                </div>
              </div>
            ))}
          </div>

          {Array.isArray(progressData.recentAchievements) && progressData.recentAchievements.length === 0 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Award className="h-8 w-8 text-gray-400" />
              </div>
              <p className="text-gray-600">Continua a studiare per sbloccare i tuoi primi obiettivi!</p>
            </div>
          )}
        </div>

        {/* Learning Insights */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Andamento Studio</h3>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Media giornaliera</span>
                <span className="text-sm font-medium text-gray-900">
                  {Array.isArray(progressData.weeklyProgress) && progressData.weeklyProgress.length > 0
                    ? Math.round(progressData.weeklyProgress.reduce((sum, day) => sum + day.minutes, 0) / 7)
                    : 0} minuti
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Sessione media</span>
                <span className="text-sm font-medium text-gray-900">
                  {progressData.sessionsCompleted > 0
                    ? Math.round(progressData.totalStudyTime / progressData.sessionsCompleted)
                    : 0} minuti
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Giorni attivi</span>
                <span className="text-sm font-medium text-gray-900">
                  {Array.isArray(progressData.weeklyProgress) ? progressData.weeklyProgress.filter(day => day.sessions > 0).length : 0}/7 questa settimana
                </span>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Obiettivi</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">Studio settimanale</span>
                  <span className="text-sm font-medium text-gray-900">
                    {Array.isArray(progressData.weeklyProgress) ? progressData.weeklyProgress.reduce((sum, day) => sum + day.minutes, 0) : 0}/300 min
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, ((Array.isArray(progressData.weeklyProgress) ? progressData.weeklyProgress.reduce((sum, day) => sum + day.minutes, 0) : 0) / 300) * 100)}%`
                    }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">Concetti imparati</span>
                  <span className="text-sm font-medium text-gray-900">
                    {progressData.conceptsLearned} concetti
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, (progressData.conceptsLearned / 20) * 100)}%`
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
