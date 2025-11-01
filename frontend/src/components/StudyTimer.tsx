'use client'

import { useState, useEffect, useRef } from 'react'
import { Play, Pause, RotateCcw, Settings, Coffee, BookOpen } from 'lucide-react'

interface TimerSession {
  id: string
  type: 'work' | 'break' | 'longBreak'
  duration: number
  startTime: Date
  endTime?: Date
  completed: boolean
}

interface TimerSettings {
  workDuration: number // minutes
  shortBreakDuration: number // minutes
  longBreakDuration: number // minutes
  longBreakInterval: number // sessions before long break
  autoStartBreaks: boolean
  autoStartWork: boolean
}

export default function StudyTimer() {
  const [settings, setSettings] = useState<TimerSettings>({
    workDuration: 25,
    shortBreakDuration: 5,
    longBreakDuration: 15,
    longBreakInterval: 4,
    autoStartBreaks: false,
    autoStartWork: false
  })

  const [showSettings, setShowSettings] = useState(false)
  const [timeLeft, setTimeLeft] = useState(settings.workDuration * 60)
  const [isRunning, setIsRunning] = useState(false)
  const [currentSession, setCurrentSession] = useState<'work' | 'break' | 'longBreak'>('work')
  const [sessionCount, setSessionCount] = useState(0)
  const [todaySessions, setTodaySessions] = useState<TimerSession[]>([])
  const [totalStudyTime, setTotalStudyTime] = useState(0)

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Load saved data from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('timerSettings')
    const savedSessions = localStorage.getItem('todaySessions')
    const savedSessionCount = localStorage.getItem('sessionCount')

    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
    if (savedSessions) {
      const sessions = JSON.parse(savedSessions)
      const today = new Date().toDateString()
      const todaySessions = sessions.filter((s: TimerSession) =>
        new Date(s.startTime).toDateString() === today
      )
      setTodaySessions(todaySessions)

      // Calculate total study time for today
      const workTime = todaySessions
        .filter(s => s.type === 'work' && s.completed)
        .reduce((acc: number, s: TimerSession) => acc + s.duration, 0)
      setTotalStudyTime(workTime)
    }
    if (savedSessionCount) {
      setSessionCount(parseInt(savedSessionCount))
    }

    // Create notification sound
    audioRef.current = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT')
  }, [])

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('timerSettings', JSON.stringify(settings))
    if (!isRunning && currentSession === 'work') {
      setTimeLeft(settings.workDuration * 60)
    }
  }, [settings, isRunning, currentSession])

  // Timer countdown logic
  useEffect(() => {
    if (isRunning && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => prev - 1)
      }, 1000)
    } else if (timeLeft === 0) {
      handleSessionComplete()
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isRunning, timeLeft])

  const handleSessionComplete = () => {
    setIsRunning(false)
    playNotificationSound()

    // Complete current session
    const completedSession: TimerSession = {
      id: Date.now().toString(),
      type: currentSession,
      duration: getDurationForSession(currentSession) * 60,
      startTime: new Date(Date.now() - getDurationForSession(currentSession) * 60000),
      endTime: new Date(),
      completed: true
    }

    // Update sessions
    const updatedSessions = [...todaySessions, completedSession]
    setTodaySessions(updatedSessions)
    localStorage.setItem('todaySessions', JSON.stringify(updatedSessions))

    // Update study time
    if (currentSession === 'work') {
      setTotalStudyTime(prev => prev + settings.workDuration * 60)
      setSessionCount(prev => {
        const newCount = prev + 1
        localStorage.setItem('sessionCount', newCount.toString())
        return newCount
      })
    }

    // Determine next session
    let nextSession: 'work' | 'break' | 'longBreak'
    if (currentSession === 'work') {
      const completedWorkSessions = todaySessions.filter(s => s.type === 'work' && s.completed).length + 1
      if (completedWorkSessions % settings.longBreakInterval === 0) {
        nextSession = 'longBreak'
      } else {
        nextSession = 'break'
      }
    } else {
      nextSession = 'work'
    }

    setCurrentSession(nextSession)
    setTimeLeft(settings[getDurationKey(nextSession)] * 60)

    // Auto-start next session if enabled
    if ((nextSession !== 'work' && settings.autoStartBreaks) ||
        (nextSession === 'work' && settings.autoStartWork)) {
      setTimeout(() => setIsRunning(true), 2000)
    }
  }

  const getDurationForSession = (session: 'work' | 'break' | 'longBreak'): number => {
    switch (session) {
      case 'work': return settings.workDuration
      case 'break': return settings.shortBreakDuration
      case 'longBreak': return settings.longBreakDuration
    }
  }

  const getDurationKey = (session: 'work' | 'break' | 'longBreak'): keyof TimerSettings => {
    switch (session) {
      case 'work': return 'workDuration'
      case 'break': return 'shortBreakDuration'
      case 'longBreak': return 'longBreakDuration'
    }
  }

  const playNotificationSound = () => {
    if (audioRef.current) {
      audioRef.current.play().catch(e => console.log('Audio play failed:', e))
    }

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'granted') {
      const message = currentSession === 'work'
        ? 'Tempo di pausa! 🎉'
        : 'Riprendi a studiare! 📚'

      new Notification('Tutor AI - Timer', {
        body: message,
        icon: '/favicon.ico'
      })
    }
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleStartPause = () => {
    setIsRunning(!isRunning)
  }

  const handleReset = () => {
    setIsRunning(false)
    setTimeLeft(settings.workDuration * 60)
    setCurrentSession('work')
  }

  const handleSkipSession = () => {
    setIsRunning(false)
    const nextSession = currentSession === 'work' ? 'break' : 'work'
    setCurrentSession(nextSession)
    setTimeLeft(settings[getDurationKey(nextSession)] * 60)
  }

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  useEffect(() => {
    requestNotificationPermission()
  }, [])

  const getSessionIcon = () => {
    switch (currentSession) {
      case 'work': return <BookOpen className="w-8 h-8 text-blue-600" />
      case 'break':
      case 'longBreak': return <Coffee className="w-8 h-8 text-emerald-600" />
    }
  }

  const getSessionLabel = () => {
    switch (currentSession) {
      case 'work': return 'Sessione di Studio'
      case 'break': return 'Pausa Breve'
      case 'longBreak': return 'Pausa Lunga'
    }
  }

  const getSessionColor = () => {
    switch (currentSession) {
      case 'work': return 'from-blue-500 to-purple-600'
      case 'break': return 'from-emerald-500 to-teal-600'
      case 'longBreak': return 'from-amber-500 to-orange-600'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-rose-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 fade-in">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Timer di Studio
          </h1>
          <p className="text-gray-600">
            Tecnica Pomodoro per massimizzare la concentrazione
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="glass-card p-6 text-center hover-lift">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {Math.floor(totalStudyTime / 3600)}h {Math.floor((totalStudyTime % 3600) / 60)}m
            </div>
            <div className="text-sm text-gray-600">Tempo di studio oggi</div>
          </div>

          <div className="glass-card p-6 text-center hover-lift">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {todaySessions.filter(s => s.type === 'work' && s.completed).length}
            </div>
            <div className="text-sm text-gray-600">Sessioni completate</div>
          </div>

          <div className="glass-card p-6 text-center hover-lift">
            <div className="text-3xl font-bold text-emerald-600 mb-2">
              {sessionCount}
            </div>
            <div className="text-sm text-gray-600">Sessioni totali</div>
          </div>
        </div>

        {/* Main Timer */}
        <div className="glass-card p-8 mb-6">
          <div className="text-center">
            {/* Session Type */}
            <div className="flex items-center justify-center mb-6">
              {getSessionIcon()}
              <h2 className="text-2xl font-semibold text-gray-800 ml-3">
                {getSessionLabel()}
              </h2>
            </div>

            {/* Timer Display */}
            <div className={`relative inline-block p-8 rounded-2xl bg-gradient-to-br ${getSessionColor()} text-white mb-8 shadow-2xl`}>
              <div className="text-6xl font-mono font-bold">
                {formatTime(timeLeft)}
              </div>

              {/* Progress Ring */}
              <svg className="absolute inset-0 w-full h-full -z-10">
                <circle
                  cx="50%"
                  cy="50%"
                  r="45%"
                  fill="none"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="4"
                />
                <circle
                  cx="50%"
                  cy="50%"
                  r="45%"
                  fill="none"
                  stroke="white"
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 0.45}`}
                  strokeDashoffset={`${2 * Math.PI * 0.45 * (1 - timeLeft / (getDurationForSession(currentSession) * 60))}`}
                  transform="rotate(-90)"
                  style={{ transformOrigin: 'center' }}
                  className="transition-all duration-1000"
                />
              </svg>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-center space-x-4 mb-6">
              <button
                onClick={handleStartPause}
                className={`btn ${isRunning ? 'btn-secondary' : 'btn-primary'} px-8 py-3`}
              >
                {isRunning ? (
                  <>
                    <Pause className="w-5 h-5" />
                    Pausa
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Inizia
                  </>
                )}
              </button>

              <button
                onClick={handleReset}
                className="btn btn-secondary px-6 py-3"
              >
                <RotateCcw className="w-5 h-5" />
                Reset
              </button>

              <button
                onClick={() => setShowSettings(!showSettings)}
                className="btn btn-secondary px-6 py-3"
              >
                <Settings className="w-5 h-5" />
                Impostazioni
              </button>
            </div>

            {/* Skip Button */}
            <button
              onClick={handleSkipSession}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Salta sessione →
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="glass-card p-6 mb-6 slide-in-up">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Impostazioni Timer</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Durata Sessione di Studio (minuti)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={settings.workDuration}
                  onChange={(e) => setSettings({...settings, workDuration: parseInt(e.target.value) || 25})}
                  className="form-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Durata Pausa Breve (minuti)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={settings.shortBreakDuration}
                  onChange={(e) => setSettings({...settings, shortBreakDuration: parseInt(e.target.value) || 5})}
                  className="form-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Durata Pausa Lunga (minuti)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={settings.longBreakDuration}
                  onChange={(e) => setSettings({...settings, longBreakDuration: parseInt(e.target.value) || 15})}
                  className="form-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pausa Lunga ogni (sessioni)
                </label>
                <input
                  type="number"
                  min="2"
                  max="10"
                  value={settings.longBreakInterval}
                  onChange={(e) => setSettings({...settings, longBreakInterval: parseInt(e.target.value) || 4})}
                  className="form-input"
                />
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.autoStartBreaks}
                  onChange={(e) => setSettings({...settings, autoStartBreaks: e.target.checked})}
                  className="mr-3"
                />
                <span className="text-sm text-gray-700">Avvia automaticamente le pause</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.autoStartWork}
                  onChange={(e) => setSettings({...settings, autoStartWork: e.target.checked})}
                  className="mr-3"
                />
                <span className="text-sm text-gray-700">Avvia automaticamente il lavoro</span>
              </label>
            </div>
          </div>
        )}

        {/* Today's Sessions */}
        <div className="glass-card p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Sessioni di Oggi</h3>

          {todaySessions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              Nessuna sessione completata oggi. Inizia a studiare!
            </p>
          ) : (
            <div className="space-y-2">
              {todaySessions.slice(-5).reverse().map((session) => (
                <div
                  key={session.id}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    session.type === 'work'
                      ? 'bg-blue-50 border border-blue-200'
                      : 'bg-emerald-50 border border-emerald-200'
                  }`}
                >
                  <div className="flex items-center">
                    {session.type === 'work' ? (
                      <BookOpen className="w-5 h-5 text-blue-600 mr-3" />
                    ) : (
                      <Coffee className="w-5 h-5 text-emerald-600 mr-3" />
                    )}
                    <span className="text-sm font-medium text-gray-700">
                      {session.type === 'work' ? 'Studio' : session.type === 'break' ? 'Pausa Breve' : 'Pausa Lunga'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {session.completed ? '✓ Completata' : 'In corso'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}