'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Calendar, Clock, BookOpen, Target, CheckCircle, Circle, Plus, Settings, Play, Edit3, Trash2, ChevronRight, BookMarked, MessageSquare } from 'lucide-react'

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

  const [newPlan, setNewPlan] = useState<NewPlanForm>({
    course_id: '',
    title: 'Piano di Studio Personalizzato',
    sessions_per_week: 3,
    session_duration: 45,
    difficulty_level: 'intermediate',
    difficulty_progression: 'graduale'
  })

  useEffect(() => {
    fetchCourses()
    fetchPlans()
  }, [])

  const fetchCourses = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/study-plans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newPlan)
      })

      const data = await response.json()
      if (data.success) {
        setPlans(prev => [data.plan, ...prev])
        setShowCreateForm(false)
        setNewPlan({
          course_id: '',
          title: 'Piano di Studio Personalizzato',
          sessions_per_week: 3,
          session_duration: 45,
          difficulty_level: 'intermediate',
          difficulty_progression: 'graduale'
        })
      } else {
        alert('Errore nella creazione del piano di studio')
      }
    } catch (error) {
      console.error('Error creating plan:', error)
      alert('Errore nella creazione del piano di studio')
    } finally {
      setCreatingPlan(false)
    }
  }

  const updateSessionProgress = async (planId: string, sessionId: string, completed: boolean) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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
      }
    } catch (error) {
      console.error('Error updating session progress:', error)
    }
  }

  const deletePlan = async (planId: string) => {
    if (!confirm('Sei sicuro di voler eliminare questo piano di studio?')) return

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'Principiante'
      case 'intermediate': return 'Intermedio'
      case 'advanced': return 'Avanzato'
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
                <p className="text-gray-600 mt-1">Crea e gestisci piani di studio personalizzati</p>
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
                    onClick={() => setSelectedPlan(plan)}
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

                              <div className="flex items-center space-x-4 text-xs text-gray-500 mb-3">
                                <span>Sessione {index + 1}</span>
                                {session.topics.length > 0 && (
                                  <span>{session.topics.length} argoment{session.topics.length === 1 ? 'o' : 'i'}</span>
                                )}
                                {session.objectives.length > 0 && (
                                  <span>{session.objectives.length} obiettiv{session.objectives.length === 1 ? 'o' : 'i'}</span>
                                )}
                              </div>

                              {expandedSessions.has(session.id) && (
                                <div className="mt-4 space-y-3 text-sm">
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
                                      <strong className="text-gray-700">Obiettivi:</strong>
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
  )
}