'use client'

import { useState, useEffect, useMemo, Fragment } from 'react'
import { useRouter } from 'next/navigation'
import { Clock, BookOpen, Target, CheckCircle, Circle, Plus, Trash2, ChevronRight, BookMarked, MessageSquare } from 'lucide-react'
import AIProviderBadge from '@/components/AIProviderBadge'

interface StudySession {
  id: string
  title: string
  description: string
  duration_minutes: number
  topics: string[]
  materials: string[]
  difficulty: string
  objectives: string[]
  prerequisites: string[]
  completion_date?: string
  completed: boolean
  order_index: number
  book_id?: string
  book_title?: string
  chapter_title?: string
  chapter_index?: number | null
  chapter_summary?: string | null
  concepts?: Array<{
    id?: string
    name: string
    chapter?: {
      title?: string
      index?: number | null
    }
    summary?: string
    related_topics?: string[]
    learning_objectives?: string[]
    suggested_reading?: string[]
    recommended_minutes?: number | null
    quiz_outline?: string[]
    quizzes?: Array<{
      id?: string
      label?: string
      difficulty?: string | null
      title?: string
      generated_at?: string
      questions?: Array<{
        question?: string
        options?: Record<string, string>
        correct?: string
      }>
    }>
  }>
  quizzes?: Array<{
    id?: string
    concept_id?: string
    concept_name?: string
    quiz_id?: string
    label?: string
    difficulty?: string | null
    title?: string
    generated_at?: string
    questions?: Array<{
      question?: string
      options?: Record<string, string>
      correct?: string
      explanation?: string
    }>
  }>
}

interface MissionTask {
  id: string
  label: string
  type: string
  target_id?: string | null
  related_session_id?: string | null
  related_concept_id?: string | null
  related_quiz_id?: string | null
  completed: boolean
  completed_at?: string | null
  badge?: string | null
}

interface StudyMission {
  id: string
  title: string
  description: string
  week_index: number
  start_date: string
  end_date: string
  progress: number
  badge?: string | null
  completed: boolean
  completed_at?: string | null
  tasks: MissionTask[]
}

interface StudyPlan {
  id: string
  course_id: string
  title: string
  description: string
  total_sessions: number
  estimated_hours: number
  difficulty_progression: string
  created_at: string
  updated_at: string
  sessions: StudySession[]
  missions?: StudyMission[]
  current_session_index: number
  is_active: boolean
}

interface Course {
  id: string
  name: string
  description: string
  subject: string
}

interface NewPlanForm {
  course_id: string
  title: string
  sessions_per_week: number
  session_duration: number
  difficulty_level: string
  difficulty_progression: string
  refresh_concept_quizzes: boolean
}

export default function StudyPlannerPage() {
  const router = useRouter()
  const [plans, setPlans] = useState<StudyPlan[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<StudyPlan | null>(null)
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set())
  const [creatingPlan, setCreatingPlan] = useState(false)
  const [activeQuiz, setActiveQuiz] = useState<{
    sessionId: string
    quiz: NonNullable<StudySession['quizzes']>[number]
  } | null>(null)
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({})
  const [quizSubmitted, setQuizSubmitted] = useState(false)
  const [quizScore, setQuizScore] = useState<{ correct: number; total: number }>({ correct: 0, total: 0 })
  const [quizStartTime, setQuizStartTime] = useState<number | null>(null)
  const [quizSubmitting, setQuizSubmitting] = useState(false)
  const [quizSubmitError, setQuizSubmitError] = useState<string | null>(null)
  const [quizSubmitSuccess, setQuizSubmitSuccess] = useState(false)
  const [updatingTaskIds, setUpdatingTaskIds] = useState<Set<string>>(new Set())
const [missions, setMissions] = useState<StudyMission[]>([])
const [missionsLoading, setMissionsLoading] = useState(false)
const [missionsError, setMissionsError] = useState('')
const [planGenerationProgress, setPlanGenerationProgress] = useState({
  stage: '',
  progress: 0,
  message: ''
})

  const normalizeMissionTask = (taskRaw: unknown, fallbackId: string): MissionTask => {
    const record = taskRaw && typeof taskRaw === 'object' ? taskRaw as Record<string, unknown> : {}
    return {
      id: record.id ? String(record.id) : fallbackId,
      label: record.label ? String(record.label) : 'Attività',
      type: record.type ? String(record.type) : 'task',
      target_id: record.target_id !== undefined && record.target_id !== null ? String(record.target_id) : undefined,
      related_session_id: record.related_session_id !== undefined && record.related_session_id !== null ? String(record.related_session_id) : undefined,
      related_concept_id: record.related_concept_id !== undefined && record.related_concept_id !== null ? String(record.related_concept_id) : undefined,
      related_quiz_id: record.related_quiz_id !== undefined && record.related_quiz_id !== null ? String(record.related_quiz_id) : undefined,
      completed: Boolean(record.completed),
      completed_at: typeof record.completed_at === 'string' ? record.completed_at : undefined,
      badge: record.badge !== undefined && record.badge !== null ? String(record.badge) : undefined
    }
  }

  const normalizeMission = (missionRaw: unknown, fallbackIndex = 0): StudyMission => {
    const record = missionRaw && typeof missionRaw === 'object' ? missionRaw as Record<string, unknown> : {}
    const missionId = record.id ? String(record.id) : `mission-${fallbackIndex}`
    const tasksRaw = Array.isArray(record.tasks) ? record.tasks : []
    const startDate = typeof record.start_date === 'string' ? record.start_date : new Date().toISOString()
    const endDate = typeof record.end_date === 'string' ? record.end_date : startDate

    return {
      id: missionId,
      title: record.title ? String(record.title) : 'Missione settimanale',
      description: record.description ? String(record.description) : '',
      week_index: typeof record.week_index === 'number' ? record.week_index : Number(record.week_index) || fallbackIndex,
      start_date: startDate,
      end_date: endDate,
      progress: typeof record.progress === 'number' ? record.progress : Number(record.progress) || 0,
      badge: record.badge !== undefined && record.badge !== null ? String(record.badge) : undefined,
      completed: Boolean(record.completed),
      completed_at: typeof record.completed_at === 'string' ? record.completed_at : undefined,
      tasks: tasksRaw.map((task, index) => normalizeMissionTask(task, `${missionId}-task-${index}`))
    }
  }

  const normalizeMissions = (missionsData: unknown[] = []): StudyMission[] => (
    (missionsData || []).map((mission, index) => normalizeMission(mission, index))
  )

  const [newPlan, setNewPlan] = useState<NewPlanForm>({
    course_id: '',
    title: 'Piano di Studio Personalizzato',
    sessions_per_week: 3,
    session_duration: 45,
    difficulty_level: 'intermediate',
    difficulty_progression: 'graduale',
    refresh_concept_quizzes: true
  })

  useEffect(() => {
    fetchCourses()
    fetchPlans()
  }, [])

  useEffect(() => {
    if (selectedPlan) {
      setMissionsError('')
      fetchMissions(selectedPlan.id, normalizeMissions(selectedPlan.missions || []))
    } else {
      setMissions([])
    }
  }, [selectedPlan?.id])

  const fetchCourses = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      const response = await fetch(`${apiUrl}/courses`)
      const data = await response.json()
      setCourses(data.courses || [])
    } catch (error) {
      console.error('Error fetching courses:', error)
    }
  }

  const fetchPlans = async () => {
    try {
      setLoading(true)
      const allPlans: StudyPlan[] = []
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

      for (const course of courses) {
        try {
          const response = await fetch(`${apiUrl}/courses/${course.id}/study-plans`)
          const data = await response.json()
          if (data.success) {
            allPlans.push(...data.plans)
          }
        } catch (error) {
          console.error(`Error fetching plans for course ${course.id}:`, error)
        }
      }

      setPlans(allPlans)
    } catch (error) {
      console.error('Error fetching plans:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchMissions = async (planId: string, fallback: StudyMission[] = []) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
    if (fallback.length > 0) {
      setMissions(fallback)
    }

    try {
      setMissionsLoading(true)
      setMissionsError('')
      const response = await fetch(`${apiUrl}/study-plans/${planId}/missions`)
      if (!response.ok) {
        throw new Error('Errore nel caricamento delle missioni')
      }
      const data = await response.json()
      if (data.success) {
        const missionsRaw = Array.isArray(data.missions) ? data.missions : []
        const normalized = normalizeMissions(missionsRaw as unknown[])
        setMissions(normalized)
        setSelectedPlan(prev => (prev && prev.id === planId) ? { ...prev, missions: normalized } : prev)
      } else {
        setMissionsError('Impossibile recuperare le missioni')
      }
    } catch (error) {
      console.error('Error fetching missions:', error)
      setMissionsError('Errore nel caricamento delle missioni settimanali')
    } finally {
      setMissionsLoading(false)
    }
  }

  const toggleMissionTask = async (missionId: string, taskId: string, completed: boolean) => {
    if (!selectedPlan) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
    const updating = new Set(updatingTaskIds)
    updating.add(taskId)
    setUpdatingTaskIds(updating)

    const previousMissions = missions
    setMissions(prev => prev.map(mission => {
      if (mission.id !== missionId) {
        return mission
      }
      return {
        ...mission,
        tasks: mission.tasks.map(task => task.id === taskId ? { ...task, completed } : task)
      }
    }))

    try {
      const response = await fetch(`${apiUrl}/study-plans/${selectedPlan.id}/missions/${missionId}/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ completed })
      })

      if (!response.ok) {
        throw new Error('Errore durante l\'aggiornamento della missione')
      }

      const data = await response.json()
      if (data.success && data.mission) {
        const normalizedMission = normalizeMissions([data.mission])[0]
        setMissions(prev => prev.map(mission => mission.id === missionId ? normalizedMission : mission))
      } else {
        throw new Error('Risposta non valida dal server')
      }
    } catch (error) {
      console.error('Error updating mission task:', error)
      setMissions(previousMissions)
    } finally {
      setUpdatingTaskIds(prev => {
        const updated = new Set(prev)
        updated.delete(taskId)
        return updated
      })
    }
  }

  const autoCompleteMissionTask = async (quizId: string) => {
    const mission = missions.find(currentMission => currentMission.tasks.some(task => task.related_quiz_id === quizId))
    if (!mission) return
    const task = mission.tasks.find(item => item.related_quiz_id === quizId)
    if (!task || task.completed) return
    await toggleMissionTask(mission.id, task.id, true)
  }

  const activeMission = useMemo(() => {
    if (!missions.length) return null
    const nextMission = missions.find(mission => !mission.completed)
    return nextMission ?? missions[missions.length - 1]
  }, [missions])

  const secondaryMissions = useMemo(() => {
    if (!missions.length) return [] as StudyMission[]
    const activeId = activeMission?.id
    return missions.filter(mission => mission.id !== activeId)
  }, [missions, activeMission?.id])

  useEffect(() => {
    if (courses.length > 0) {
      fetchPlans()
    }
  }, [courses])

  const createStudyPlan = async () => {
    if (!newPlan.course_id) {
      alert('Seleziona un corso')
      return
    }

    try {
      setCreatingPlan(true)
      console.log('🚀 Inizio creazione piano di studio...')
      setPlanGenerationProgress({
        stage: 'initialization',
        progress: 10,
        message: 'Inizializzazione creazione piano...'
      })

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      console.log('📡 Invio richiesta al backend:', apiUrl)
      setPlanGenerationProgress({
        stage: 'request',
        progress: 25,
        message: 'Invio richiesta al server...'
      })

      const response = await fetch(`${apiUrl}/study-plans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newPlan)
      })

      console.log('📡 Risposta ricevuta, stato:', response.status)
      setPlanGenerationProgress({
        stage: 'processing',
        progress: 50,
        message: 'Elaborazione dati in corso...'
      })

      const data = await response.json()
      console.log('📊 Dati ricevuti:', data)

      setPlanGenerationProgress({
        stage: 'finalization',
        progress: 75,
        message: 'Finalizzazione piano...'
      })

      if (data.success) {
        console.log('✅ Piano creato con successo!')
        const createdPlan: StudyPlan = data.plan
        console.log('📋 Dettagli piano:', {
          id: createdPlan.id,
          title: createdPlan.title,
          sessions: createdPlan.total_sessions,
          missions: createdPlan.missions?.length || 0
        })

        setPlans(prev => [createdPlan, ...prev])
        setShowCreateForm(false)
        setNewPlan({
          course_id: '',
          title: 'Piano di Studio Personalizzato',
          sessions_per_week: 3,
          session_duration: 45,
          difficulty_level: 'intermediate',
          difficulty_progression: 'graduale',
          refresh_concept_quizzes: true
        })
        setSelectedPlan(createdPlan)
        setMissions(normalizeMissions(createdPlan.missions || []))
        setMissionsError('')
        setExpandedSessions(new Set())

        setPlanGenerationProgress({
          stage: 'completed',
          progress: 100,
          message: 'Piano creato con successo!'
        })

        setTimeout(() => {
          setPlanGenerationProgress({ stage: '', progress: 0, message: '' })
        }, 2000)
      } else {
        console.error('❌ Errore dal backend:', data)
        setPlanGenerationProgress({
          stage: 'error',
          progress: 0,
          message: 'Errore nella creazione del piano'
        })
        alert('Errore nella creazione del piano di studio')
      }
    } catch (error) {
      console.error('💥 Errore durante la creazione del piano:', error)
      setPlanGenerationProgress({
        stage: 'error',
        progress: 0,
        message: 'Errore di connessione al server'
      })
      alert('Errore nella creazione del piano di studio')
    } finally {
      setCreatingPlan(false)
    }
  }

  const updateSessionProgress = async (planId: string, sessionId: string, completed: boolean) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      const response = await fetch(`${apiUrl}/study-plans/${planId}/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ completed })
      })

      if (response.ok) {
        setPlans(prev => prev.map(plan =>
          plan.id === planId
            ? {
                ...plan,
                sessions: plan.sessions.map(session =>
                  session.id === sessionId ? { ...session, completed, completion_date: completed ? new Date().toISOString() : undefined } : session
                )
              }
            : plan
        ))
        void fetchMissions(planId)
      }
    } catch (error) {
      console.error('Error updating session progress:', error)
    }
  }

  const deletePlan = async (planId: string) => {
    if (!confirm('Sei sicuro di voler eliminare questo piano di studio?')) return

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      const response = await fetch(`${apiUrl}/study-plans/${planId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        setPlans(prev => prev.filter(plan => plan.id !== planId))
        if (selectedPlan?.id === planId) {
          setSelectedPlan(null)
        }
      }
    } catch (error) {
      console.error('Error deleting plan:', error)
    }
  }

  const toggleSessionExpansion = (sessionId: string) => {
    setExpandedSessions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sessionId)) {
        newSet.delete(sessionId)
      } else {
        newSet.add(sessionId)
      }
      return newSet
    })
  }

  const getCourseName = (courseId: string) => {
    const course = courses.find(c => c.id === courseId)
    return course?.name || 'Corso sconosciuto'
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      case 'easy': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'hard': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'Principiante'
      case 'intermediate': return 'Intermedio'
      case 'advanced': return 'Avanzato'
      case 'easy': return 'Facile'
      case 'medium': return 'Medio'
      case 'hard': return 'Difficile'
      default: return difficulty
    }
  }

  const startSession = (planId: string, sessionId: string, sessionTitle: string, courseId: string) => {
    const params = new URLSearchParams({
      planId,
      courseId,
      sessionTitle
    })
    router.push(`/study-planner/${sessionId}?${params.toString()}`)
  }

  const openQuiz = (sessionId: string, quiz: NonNullable<StudySession['quizzes']>[number]) => {
    setActiveQuiz({ sessionId, quiz })
    setQuizAnswers({})
    setQuizSubmitted(false)
    setQuizScore({ correct: 0, total: quiz.questions?.length ?? 0 })
    setQuizStartTime(Date.now())
    setQuizSubmitting(false)
    setQuizSubmitError(null)
    setQuizSubmitSuccess(false)
  }

  const closeQuiz = () => {
    setActiveQuiz(null)
    setQuizAnswers({})
    setQuizSubmitted(false)
    setQuizScore({ correct: 0, total: 0 })
    setQuizStartTime(null)
    setQuizSubmitting(false)
    setQuizSubmitError(null)
    setQuizSubmitSuccess(false)
  }

  const handleQuizAnswerChange = (questionIndex: number, optionKey: string) => {
    setQuizAnswers(prev => ({
      ...prev,
      [questionIndex]: optionKey
    }))
  }

  const submitQuizAnswers = async () => {
    if (!activeQuiz?.quiz.questions || quizSubmitting) {
      return
    }

    const total = activeQuiz.quiz.questions.length
    let correct = 0
    activeQuiz.quiz.questions.forEach((question, index) => {
      const userAnswer = quizAnswers[index]
      if (userAnswer && question.correct && userAnswer === question.correct) {
        correct += 1
      }
    })

    setQuizScore({ correct, total })
    setQuizSubmitted(true)
    setQuizSubmitting(true)
    setQuizSubmitError(null)

    const courseId = selectedPlan?.course_id
    const conceptId = activeQuiz.quiz.concept_id
    if (!courseId || !conceptId) {
      setQuizSubmitting(false)
      setQuizSubmitError('Impossibile registrare il risultato del quiz (informazioni corso o concetto mancanti).')
      return
    }

    const session = selectedPlan.sessions.find(s => s.id === activeQuiz.sessionId)
    const timeSeconds = quizStartTime ? (Date.now() - quizStartTime) / 1000 : 0
    const scoreRatio = total > 0 ? correct / total : 0
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

    try {
      const response = await fetch(`${apiUrl}/courses/${courseId}/concepts/${conceptId}/quiz-results`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          concept_name: activeQuiz.quiz.concept_name || session?.chapter_title || activeQuiz.quiz.title || 'Concetto',
          chapter_title: session?.chapter_title ?? null,
          score: Number(scoreRatio.toFixed(3)),
          time_seconds: Number(timeSeconds.toFixed(2)),
          correct_answers: correct,
          total_questions: total
        })
      })

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}))
        throw new Error(detail?.detail || 'Errore nella registrazione del risultato')
      }

      setQuizSubmitSuccess(true)
      const quizId = activeQuiz.quiz.quiz_id || activeQuiz.quiz.id
      if (quizId) {
        void autoCompleteMissionTask(String(quizId))
      }
    } catch (error) {
      console.error('Errore nel salvataggio del quiz:', error)
      setQuizSubmitError(error instanceof Error ? error.message : 'Errore nel salvataggio del quiz')
    } finally {
      setQuizSubmitting(false)
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
          <p className="mt-4 text-gray-600 font-medium animate-pulse">Caricamento piani di studio...</p>
        </div>
      </div>
    )
  }

  return (
    <Fragment>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="container-responsive py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                <BookMarked className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Piani di Studio</h1>
                <div className="flex items-center space-x-3 mt-1">
                  <p className="text-gray-600">Crea e gestisci piani di studio personalizzati</p>
                  <AIProviderBadge showDetails={false} />
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <Plus className="h-5 w-5" />
              <span>Nuovo Piano</span>
            </button>
          </div>
        </div>

        {/* Create Plan Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h3 className="text-xl font-bold mb-4">Crea Nuovo Piano di Studio</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Corso
                  </label>
                  <select
                    value={newPlan.course_id}
                    onChange={(e) => setNewPlan(prev => ({ ...prev, course_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Seleziona un corso</option>
                    {courses.map(course => (
                      <option key={course.id} value={course.id}>{course.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Titolo
                  </label>
                  <input
                    type="text"
                    value={newPlan.title}
                    onChange={(e) => setNewPlan(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sessioni per settimana
                    </label>
                    <select
                      value={newPlan.sessions_per_week}
                      onChange={(e) => setNewPlan(prev => ({ ...prev, sessions_per_week: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={2}>2</option>
                      <option value={3}>3</option>
                      <option value={4}>4</option>
                      <option value={5}>5</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Durata sessione (minuti)
                    </label>
                    <select
                      value={newPlan.session_duration}
                      onChange={(e) => setNewPlan(prev => ({ ...prev, session_duration: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={30}>30</option>
                      <option value={45}>45</option>
                      <option value={60}>60</option>
                      <option value={90}>90</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Livello difficoltà
                    </label>
                    <select
                      value={newPlan.difficulty_level}
                      onChange={(e) => setNewPlan(prev => ({ ...prev, difficulty_level: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="beginner">Principiante</option>
                      <option value="intermediate">Intermedio</option>
                      <option value="advanced">Avanzato</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Progressione
                    </label>
                    <select
                      value={newPlan.difficulty_progression}
                      onChange={(e) => setNewPlan(prev => ({ ...prev, difficulty_progression: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="graduale">Graduale</option>
                      <option value="lineare">Lineare</option>
                      <option value="intensivo">Intensivo</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-start space-x-3 rounded-lg border border-blue-100 bg-blue-50 px-3 py-3">
                  <input
                    id="refresh-concept-quizzes"
                    type="checkbox"
                    checked={newPlan.refresh_concept_quizzes}
                    onChange={(e) => setNewPlan(prev => ({ ...prev, refresh_concept_quizzes: e.target.checked }))}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="refresh-concept-quizzes" className="text-sm text-gray-700">
                    <span className="block font-medium">Rigenera i quiz per ogni concetto</span>
                    <span className="text-xs text-gray-600">
                      Genera quiz diagnostici e di approfondimento per monitorare la comprensione di ogni capitolo.
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={createStudyPlan}
                  disabled={creatingPlan || !newPlan.course_id}
                  className="flex-1 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {creatingPlan ? 'Creazione...' : 'Crea Piano'}
                </button>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Annulla
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Plan Generation Progress Modal */}
        {creatingPlan && planGenerationProgress.stage && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <div className="text-center">
                <div className="mb-4">
                  <div className="relative mx-auto w-16 h-16">
                    <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                    <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-t-purple-600 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                  </div>
                </div>

                <h3 className="text-xl font-bold mb-2 text-gray-900">
                  {planGenerationProgress.stage === 'completed' ? 'Piano Creato!' :
                   planGenerationProgress.stage === 'error' ? 'Errore' :
                   'Creazione Piano in Corso...'}
                </h3>

                <p className="text-gray-600 mb-4">
                  {planGenerationProgress.message}
                </p>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${
                      planGenerationProgress.stage === 'completed' ? 'bg-green-500' :
                      planGenerationProgress.stage === 'error' ? 'bg-red-500' :
                      'bg-gradient-to-r from-blue-500 to-purple-600'
                    }`}
                    style={{ width: `${planGenerationProgress.progress}%` }}
                  ></div>
                </div>

                {/* Stage indicators */}
                <div className="space-y-2 text-sm text-gray-600">
                  <div className={`flex items-center space-x-2 ${
                    ['initialization', 'request', 'processing', 'finalization', 'completed', 'error'].includes(planGenerationProgress.stage) ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      planGenerationProgress.progress >= 10 ? 'bg-blue-600' : 'bg-gray-300'
                    }`}></div>
                    <span>Inizializzazione</span>
                  </div>
                  <div className={`flex items-center space-x-2 ${
                    ['request', 'processing', 'finalization', 'completed', 'error'].includes(planGenerationProgress.stage) ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      planGenerationProgress.progress >= 25 ? 'bg-blue-600' : 'bg-gray-300'
                    }`}></div>
                    <span>Invio richiesta</span>
                  </div>
                  <div className={`flex items-center space-x-2 ${
                    ['processing', 'finalization', 'completed', 'error'].includes(planGenerationProgress.stage) ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      planGenerationProgress.progress >= 50 ? 'bg-blue-600' : 'bg-gray-300'
                    }`}></div>
                    <span>Elaborazione</span>
                  </div>
                  <div className={`flex items-center space-x-2 ${
                    ['finalization', 'completed', 'error'].includes(planGenerationProgress.stage) ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      planGenerationProgress.progress >= 75 ? 'bg-blue-600' : 'bg-gray-300'
                    }`}></div>
                    <span>Finalizzazione</span>
                  </div>
                  <div className={`flex items-center space-x-2 ${
                    planGenerationProgress.stage === 'completed' ? 'text-green-600' :
                    planGenerationProgress.stage === 'error' ? 'text-red-600' : 'text-gray-400'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      planGenerationProgress.progress >= 100 ? 'bg-green-600' :
                      planGenerationProgress.stage === 'error' ? 'bg-red-600' : 'bg-gray-300'
                    }`}></div>
                    <span>
                      {planGenerationProgress.stage === 'completed' ? 'Completato' :
                       planGenerationProgress.stage === 'error' ? 'Errore' : 'In attesa'}
                    </span>
                  </div>
                </div>

                {planGenerationProgress.stage === 'error' && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600">
                      Si è verificato un errore durante la creazione del piano. Riprova più tardi.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {plans.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <BookMarked className="h-12 w-12 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Nessun piano di studio</h3>
            <p className="text-gray-600 mb-6">Crea il tuo primo piano di studio personalizzato per iniziare a organizzare il tuo apprendimento.</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200"
            >
              <Plus className="h-5 w-5" />
              <span>Crea il tuo primo piano</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Plans List */}
            <div className="lg:col-span-1">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">I Tuoi Piani</h2>
              <div className="space-y-4">
                {plans.map(plan => (
                  <div
                    key={plan.id}
                    className={`glass-card p-4 cursor-pointer transition-all duration-200 ${
                      selectedPlan?.id === plan.id ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
                    }`}
                    onClick={() => {
                      setSelectedPlan(plan)
                      setMissions(normalizeMissions(plan.missions || []))
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 text-sm">{plan.title}</h3>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          deletePlan(plan.id)
                        }}
                        className="text-red-500 hover:text-red-700 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{getCourseName(plan.course_id)}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">{plan.total_sessions} sessioni</span>
                      <span className="text-gray-500">{plan.estimated_hours} ore</span>
                    </div>
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-gray-500">Progresso</span>
                        <span className="font-medium text-gray-700">
                          {plan.sessions.filter(s => s.completed).length}/{plan.total_sessions}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-600 h-1.5 rounded-full transition-all duration-300"
                          style={{
                            width: `${(plan.sessions.filter(s => s.completed).length / plan.total_sessions) * 100}%`
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Plan Details */}
            <div className="lg:col-span-2">
              {selectedPlan ? (
                <div>
                  <div className="glass-card p-6 mb-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedPlan.title}</h2>
                        <p className="text-gray-600 mb-4">{selectedPlan.description}</p>
                        <div className="flex items-center space-x-4 text-sm">
                          <div className="flex items-center space-x-1">
                            <BookOpen className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-600">{getCourseName(selectedPlan.course_id)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-600">{selectedPlan.estimated_hours} ore totali</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Target className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-600">{selectedPlan.total_sessions} sessioni</span>
                          </div>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getDifficultyColor(selectedPlan.sessions[0]?.difficulty || 'intermediate')}`}>
                        {getDifficultyLabel(selectedPlan.sessions[0]?.difficulty || 'intermediate')}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {selectedPlan.sessions.filter(s => s.completed).length}
                        </div>
                        <div className="text-sm text-gray-600">Sessioni completate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {selectedPlan.total_sessions - selectedPlan.sessions.filter(s => s.completed).length}
                        </div>
                        <div className="text-sm text-gray-600">Sessioni rimanenti</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {Math.round((selectedPlan.sessions.filter(s => s.completed).length / selectedPlan.total_sessions) * 100)}%
                        </div>
                        <div className="text-sm text-gray-600">Progresso totale</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 space-y-4">
                    {missionsLoading ? (
                      <div className="glass-card p-4 flex items-center space-x-3 text-sm text-gray-600">
                        <div className="w-4 h-4 border-2 border-blue-300 border-t-blue-600 rounded-full animate-spin"></div>
                        <span>Caricamento missioni settimanali...</span>
                      </div>
                    ) : missionsError ? (
                      <div className="glass-card p-4 border border-red-200 text-red-600 text-sm">
                        {missionsError}
                      </div>
                    ) : activeMission ? (
                      <div className="glass-card p-5">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                              <span>{activeMission.title}</span>
                              {activeMission.badge && (
                                <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">
                                  {activeMission.badge}
                                </span>
                              )}
                            </h3>
                            <p className="text-sm text-gray-600 mt-1">{activeMission.description}</p>
                            <p className="text-xs text-gray-500 mt-2">
                              {new Date(activeMission.start_date).toLocaleDateString()} → {new Date(activeMission.end_date).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs uppercase text-gray-500">Avanzamento</p>
                            <p className="text-lg font-semibold text-gray-900">{Math.round((activeMission.progress || 0) * 100)}%</p>
                          </div>
                        </div>

                        <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-blue-500"
                            style={{ width: `${Math.round((activeMission.progress || 0) * 100)}%` }}
                          ></div>
                        </div>

                        <div className="mt-4 space-y-2">
                          {activeMission.tasks.map(task => (
                            <label key={task.id} className="flex items-start space-x-3 text-sm text-gray-700">
                              <input
                                type="checkbox"
                                checked={task.completed}
                                disabled={updatingTaskIds.has(task.id)}
                                onChange={(e) => toggleMissionTask(activeMission.id, task.id, e.target.checked)}
                                className="mt-1 h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                              />
                              <div className={task.completed ? 'text-gray-400 line-through' : ''}>
                                <span className="font-medium">{task.label}</span>
                                <div className="text-xs text-gray-500">
                                  {task.type === 'session' && 'Sessione'}
                                  {task.type === 'quiz' && 'Quiz'}
                                  {task.type === 'concept_review' && 'Ripasso concetto'}
                                </div>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="glass-card p-4 text-sm text-gray-600">
                        Nessuna missione disponibile per questo piano.
                      </div>
                    )}

                    {secondaryMissions.length > 0 && (
                      <div className="glass-card p-4">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">Altre missioni</h4>
                        <div className="space-y-2 text-sm text-gray-600">
                          {secondaryMissions.map(mission => (
                            <div key={mission.id} className="flex items-center justify-between">
                              <div>
                                <p className="font-medium text-gray-700">{mission.title}</p>
                                <p className="text-xs text-gray-500">
                                  {new Date(mission.start_date).toLocaleDateString()} → {new Date(mission.end_date).toLocaleDateString()}
                                </p>
                              </div>
                              <span className="text-xs px-2 py-0.5 rounded-full border border-gray-200">
                                {Math.round((mission.progress || 0) * 100)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Sessions List */}
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Sessioni di Studio</h3>
                    <div className="space-y-4">
                      {selectedPlan.sessions.map((session, index) => (
                        <div
                          key={session.id}
                          className={`glass-card p-4 transition-all duration-200 ${
                            session.completed ? 'bg-green-50 border-green-200' : 'hover:shadow-md'
                          }`}
                        >
                          <div className="flex items-start space-x-4">
                            <button
                              onClick={() => updateSessionProgress(selectedPlan.id, session.id, !session.completed)}
                              className="mt-1 flex-shrink-0"
                            >
                              {session.completed ? (
                                <CheckCircle className="h-6 w-6 text-green-600" />
                              ) : (
                                <Circle className="h-6 w-6 text-gray-400 hover:text-blue-600 transition-colors" />
                              )}
                            </button>

                            <div className="flex-1">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <h4 className="font-semibold text-gray-900">{session.title}</h4>
                                  <p className="text-sm text-gray-600 mt-1">{session.description}</p>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <button
                                    onClick={() => startSession(selectedPlan.id, session.id, session.title, selectedPlan.course_id)}
                                    className="flex items-center space-x-1 px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium shadow-sm hover:shadow-md"
                                  >
                                    <MessageSquare className="h-3 w-3" />
                                    <span>Avvia</span>
                                  </button>
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(session.difficulty)}`}>
                                    {getDifficultyLabel(session.difficulty)}
                                  </span>
                                  <span className="text-sm text-gray-500 flex items-center">
                                    <Clock className="h-3 w-3 mr-1" />
                                    {session.duration_minutes}min
                                  </span>
                                </div>
                              </div>

                              <div className="mt-3 space-y-2">
                                <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                                  <span>Sessione {index + 1}</span>
                                  {session.topics.length > 0 && (
                                    <span>{session.topics.length} argoment{session.topics.length === 1 ? 'o' : 'i'}</span>
                                  )}
                                  {session.objectives.length > 0 && (
                                    <span>{session.objectives.length} obiettiv{session.objectives.length === 1 ? 'o' : 'i'}</span>
                                  )}
                                  {session.concepts && session.concepts.length > 0 && (
                                    <span>{session.concepts.length} concett{session.concepts.length === 1 ? 'o' : 'i'}</span>
                                  )}
                                  {session.quizzes && session.quizzes.length > 0 && (
                                    <span>{session.quizzes.length} quiz</span>
                                  )}
                                </div>
                                {(typeof session.chapter_index === 'number' || session.book_title || session.chapter_title) && (
                                  <div className="flex flex-wrap gap-2 text-xs">
                                    {typeof session.chapter_index === 'number' && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-600 font-medium">
                                        Capitolo {session.chapter_index + 1}
                                      </span>
                                    )}
                                    {session.book_title && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-indigo-100 text-indigo-600 font-medium">
                                        Libro: {session.book_title}
                                      </span>
                                    )}
                                    {session.chapter_title && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-purple-100 text-purple-600 font-medium">
                                        {session.chapter_title}
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>

                              {expandedSessions.has(session.id) && (
                                <div className="mt-4 space-y-4 text-sm">
                                  {session.chapter_summary && (
                                    <div>
                                      <strong className="text-gray-700">Sintesi del capitolo:</strong>
                                      <p className="mt-1 text-gray-600 leading-relaxed">{session.chapter_summary}</p>
                                    </div>
                                  )}

                                  {session.concepts && session.concepts.length > 0 && (
                                    <div>
                                      <strong className="text-gray-700">Concetti chiave:</strong>
                                      <div className="mt-2 space-y-3">
                                        {session.concepts.map((concept, conceptIndex) => {
                                          if (!concept) return null
                                          return (
                                            <div
                                              key={`${concept.id || concept.name || 'concept'}-${conceptIndex}`}
                                              className="rounded-lg border border-gray-200 bg-white/60 p-3 shadow-sm"
                                            >
                                              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                                                <div>
                                                  <div className="font-medium text-gray-800">{concept.name}</div>
                                                  {concept.summary && (
                                                    <p className="mt-1 text-gray-600 text-sm leading-relaxed">{concept.summary}</p>
                                                  )}
                                                </div>
                                                <div className="flex flex-col items-start gap-1 text-xs text-gray-500 sm:items-end">
                                                  {typeof concept.recommended_minutes === 'number' && concept.recommended_minutes > 0 && (
                                                    <span className="inline-flex items-center gap-1">
                                                      <Clock className="h-3 w-3 text-gray-400" />
                                                      {concept.recommended_minutes} min consigliati
                                                    </span>
                                                  )}
                                                  {concept.quizzes && concept.quizzes.length > 0 && (
                                                    <span className="inline-flex items-center gap-1 text-purple-600">
                                                      <BookOpen className="h-3 w-3" />
                                                      {concept.quizzes.length} quiz
                                                    </span>
                                                  )}
                                                </div>
                                              </div>
                                              {concept.related_topics && concept.related_topics.length > 0 && (
                                                <div className="mt-2 flex flex-wrap gap-2">
                                                  {concept.related_topics.slice(0, 6).map((topic, topicIndex) => (
                                                    <span
                                                      key={`${topic}-${topicIndex}`}
                                                      className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-100 text-blue-600 text-xs"
                                                    >
                                                      {topic}
                                                    </span>
                                                  ))}
                                                </div>
                                              )}
                                              {concept.learning_objectives && concept.learning_objectives.length > 0 && (
                                                <div className="mt-2">
                                                  <span className="text-xs uppercase tracking-wide text-gray-500">Obiettivi specifici</span>
                                                  <ul className="mt-1 ml-4 list-disc space-y-1 text-gray-600 text-sm">
                                                    {concept.learning_objectives.slice(0, 3).map((objective, objIndex) => (
                                                      <li key={`${objective}-${objIndex}`}>{objective}</li>
                                                    ))}
                                                  </ul>
                                                </div>
                                              )}
                                              {concept.suggested_reading && concept.suggested_reading.length > 0 && (
                                                <div className="mt-2 text-xs text-gray-500">
                                                  <span className="uppercase tracking-wide">Letture consigliate:</span>
                                                  <ul className="mt-1 ml-4 list-disc space-y-1">
                                                    {concept.suggested_reading.slice(0, 3).map((reading, readingIndex) => (
                                                      <li key={`${reading}-${readingIndex}`}>{reading}</li>
                                                    ))}
                                                  </ul>
                                                </div>
                                              )}
                                            </div>
                                          )
                                        })}
                                      </div>
                                    </div>
                                  )}

                                  {session.topics.length > 0 && (
                                    <div>
                                      <strong className="text-gray-700">Argomenti:</strong>
                                      <ul className="mt-1 ml-4 list-disc text-gray-600">
                                        {session.topics.map((topic, i) => (
                                          <li key={i}>{topic}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {session.objectives.length > 0 && (
                                    <div>
                                      <strong className="text-gray-700">Obiettivi della sessione:</strong>
                                      <ul className="mt-1 ml-4 list-disc text-gray-600">
                                        {session.objectives.map((objective, i) => (
                                          <li key={i}>{objective}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {session.prerequisites.length > 0 && (
                                    <div>
                                      <strong className="text-gray-700">Prerequisiti:</strong>
                                      <ul className="mt-1 ml-4 list-disc text-gray-600">
                                        {session.prerequisites.map((prereq, i) => (
                                          <li key={i}>{prereq}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {session.materials.length > 0 && (
                                    <div>
                                      <strong className="text-gray-700">Materiali:</strong>
                                      <ul className="mt-1 ml-4 list-disc text-gray-600">
                                        {session.materials.map((material, i) => (
                                          <li key={i}>{material}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {session.quizzes && session.quizzes.length > 0 && (
                                    <div>
                                      <strong className="text-gray-700">Quiz disponibili:</strong>
                                      <div className="mt-2 space-y-2">
                                        {session.quizzes.map((quiz, quizIndex) => {
                                          const questionCount = quiz.questions?.length ?? 0
                                          const parsedDate = quiz.generated_at ? Date.parse(quiz.generated_at) : NaN
                                          const readableDate = Number.isNaN(parsedDate) ? null : new Date(parsedDate).toLocaleDateString()
                                          return (
                                            <div
                                              key={`${quiz.quiz_id || quiz.label || 'quiz'}-${quizIndex}`}
                                              className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 text-sm text-purple-700"
                                            >
                                              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                                <div>
                                                  <div className="font-medium">
                                                    {quiz.title || `${quiz.label ? quiz.label.charAt(0).toUpperCase() + quiz.label.slice(1) : 'Quiz'}${quiz.concept_name ? ` · ${quiz.concept_name}` : ''}`}
                                                  </div>
                                                  <div className="text-xs text-purple-600">
                                                    {quiz.concept_name ? `Concetto: ${quiz.concept_name}` : 'Valutazione generale'}
                                                    {quiz.label && ` · ${quiz.label.charAt(0).toUpperCase() + quiz.label.slice(1)}`}
                                                  </div>
                                                </div>
                                                {quiz.difficulty && (
                                                  <span className={`self-start rounded-full px-2 py-0.5 text-xs font-medium ${getDifficultyColor(quiz.difficulty)}`}>
                                                    {getDifficultyLabel(quiz.difficulty)}
                                                  </span>
                                                )}
                                              </div>
                                              <div className="mt-1 flex flex-wrap gap-3 text-xs text-purple-600">
                                                <span>{questionCount} domanda{questionCount === 1 ? '' : 'e'}</span>
                                                {readableDate && <span>Generato il {readableDate}</span>}
                                              </div>
                                              <div className="mt-3">
                                                <button
                                                  type="button"
                                                  onClick={() => openQuiz(session.id, quiz)}
                                                  className="inline-flex items-center space-x-2 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-purple-700"
                                                >
                                                  <span>Apri quiz</span>
                                                </button>
                                              </div>
                                            </div>
                                          )
                                        })}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}

                              <button
                                onClick={() => toggleSessionExpansion(session.id)}
                                className="mt-3 flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
                              >
                                <ChevronRight className={`h-4 w-4 transition-transform ${
                                  expandedSessions.has(session.id) ? 'rotate-90' : ''
                                }`} />
                                <span>{expandedSessions.has(session.id) ? 'Meno dettagli' : 'Più dettagli'}</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BookMarked className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Seleziona un piano di studio</h3>
                  <p className="text-gray-600">Scegli un piano dalla lista per vedere i dettagli e le sessioni.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      </div>
      {activeQuiz && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6">
          <div className="w-full max-w-2xl rounded-xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {activeQuiz.quiz.title || 'Quiz'}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {activeQuiz.quiz.concept_name
                    ? `Concetto: ${activeQuiz.quiz.concept_name}`
                    : 'Valutazione concettuale'}
                </p>
              </div>
              <button
                type="button"
                onClick={closeQuiz}
                className="text-gray-400 hover:text-gray-600"
                aria-label="Chiudi quiz"
              >
                ×
              </button>
            </div>
            <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-1">
              {(activeQuiz.quiz.questions || []).map((question, index) => {
                const options = question.options || {}
                const optionKeys = Object.keys(options)
                const userAnswer = quizAnswers[index]
                const isCorrect = quizSubmitted && userAnswer === question.correct
                const showCorrect = quizSubmitted && question.correct
                return (
                  <div key={`${activeQuiz.quiz.quiz_id || 'quiz'}-q-${index}`} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-sm font-semibold text-gray-800">
                          Domanda {index + 1}
                        </div>
                        <p className="mt-1 text-sm text-gray-700">{question.question || 'Domanda non disponibile'}</p>
                      </div>
                      {quizSubmitted && (
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            isCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {isCorrect ? 'Corretto' : 'Risposta errata'}
                        </span>
                      )}
                    </div>
                    <div className="mt-3 space-y-2">
                      {optionKeys.length === 0 && (
                        <p className="text-xs text-gray-500">Opzioni non disponibili.</p>
                      )}
                      {optionKeys.map(optionKey => {
                        const optionLabel = options[optionKey]
                        const isSelected = userAnswer === optionKey
                        const isCorrectOption = quizSubmitted && question.correct === optionKey
                        const optionStateClass = quizSubmitted
                          ? isCorrectOption
                            ? 'border-green-500 bg-green-50'
                            : isSelected
                              ? 'border-red-400 bg-red-50'
                              : 'border-gray-200'
                          : 'border-gray-200 hover:border-purple-400'
                        return (
                          <label
                            key={optionKey}
                            className={`flex cursor-pointer items-start space-x-3 rounded-lg border px-3 py-2 text-sm transition-colors ${optionStateClass}`}
                          >
                            <input
                              type="radio"
                              name={`quiz-${activeQuiz.quiz.quiz_id}-${index}`}
                              value={optionKey}
                              checked={isSelected}
                              onChange={() => handleQuizAnswerChange(index, optionKey)}
                              disabled={quizSubmitted}
                              className="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-gray-700">
                              <span className="font-semibold">{optionKey})</span> {optionLabel}
                            </span>
                          </label>
                        )
                      })}
                    </div>
                    {showCorrect && question.correct && (
                      <div className="mt-2 text-xs text-gray-600">
                        Risposta corretta: {question.correct}
                      </div>
                    )}
                    {quizSubmitted && question.explanation && (
                      <div className="mt-2 rounded-md bg-purple-50 p-2 text-xs text-purple-700">
                        {question.explanation}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-1">
                {quizSubmitted ? (
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      Punteggio: {quizScore.correct} / {quizScore.total} ({quizScore.total > 0 ? Math.round((quizScore.correct / quizScore.total) * 100) : 0}%)
                    </p>
                    {quizSubmitSuccess && (
                      <p className="text-xs text-green-600 mt-1">
                        Risultato salvato nella cronologia dei concetti.
                      </p>
                    )}
                    {quizSubmitError && (
                      <p className="text-xs text-red-600 mt-1">
                        {quizSubmitError}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">
                    Seleziona una risposta per ogni domanda e premi “Invia risposte” per verificare il punteggio.
                  </p>
                )}
              </div>
              <div className="flex items-center gap-3">
                {!quizSubmitted && (
                  <button
                    type="button"
                    onClick={submitQuizAnswers}
                    className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-50"
                    disabled={
                      quizSubmitting ||
                      !activeQuiz.quiz.questions ||
                      activeQuiz.quiz.questions.length === 0 ||
                      Object.keys(quizAnswers).length !== activeQuiz.quiz.questions.length
                    }
                  >
                    {quizSubmitting ? 'Salvataggio...' : 'Invia risposte'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={closeQuiz}
                  className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:opacity-50"
                  disabled={quizSubmitting}
                >
                  Chiudi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Fragment>
  )
}
