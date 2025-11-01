'use client'

import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, Clock, BookOpen, Target, Award, Calendar, Brain } from 'lucide-react'

export default function ProgressPage() {
  const [progressData, setProgressData] = useState({
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
      // Simulate API call - replace with actual endpoint
      await new Promise(resolve => setTimeout(resolve, 1000))

      setProgressData({
        totalStudyTime: 1450, // minutes
        sessionsCompleted: 23,
        coursesInProgress: 3,
        conceptsLearned: 87,
        weeklyProgress: [
          { day: 'Lun', minutes: 45, sessions: 1 },
          { day: 'Mar', minutes: 30, sessions: 1 },
          { day: 'Mer', minutes: 90, sessions: 2 },
          { day: 'Gio', minutes: 60, sessions: 1 },
          { day: 'Ven', minutes: 120, sessions: 2 },
          { day: 'Sab', minutes: 45, sessions: 1 },
          { day: 'Dom', minutes: 30, sessions: 1 }
        ],
        recentAchievements: [
          { title: 'Prima Settimana Completa', description: 'Hai studiato per 7 giorni consecutivi', icon: '🔥', date: '2025-10-28' },
          { title: 'Maratona di Studio', description: 'Oltre 2 ore di studio in una giornata', icon: '⚡', date: '2025-10-25' },
          { title: 'Esploratore di Concetti', description: 'Hai imparato 50+ nuovi concetti', icon: '🎯', date: '2025-10-22' }
        ]
      })
    } catch (error) {
      console.error('Errore nel caricamento dei dati di progresso:', error)
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

  const maxMinutes = Math.max(...progressData.weeklyProgress.map(day => day.minutes))

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
            {progressData.weeklyProgress.map((day) => (
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
                {progressData.weeklyProgress.reduce((sum, day) => sum + day.minutes, 0)} minuti
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
            {progressData.recentAchievements.map((achievement, index) => (
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

          {progressData.recentAchievements.length === 0 && (
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
                <span className="text-sm font-medium text-gray-900">65 minuti</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Sessione media</span>
                <span className="text-sm font-medium text-gray-900">28 minuti</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Giorni attivi</span>
                <span className="text-sm font-medium text-gray-900">7/7 questa settimana</span>
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
                  <span className="text-sm font-medium text-gray-900">420/300 min</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">Concetti nuovi</span>
                  <span className="text-sm font-medium text-gray-900">12/20</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '60%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}