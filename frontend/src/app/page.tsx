'use client'

import { useState, useEffect } from 'react'
import { BookOpen, Brain, TrendingUp, Clock, Plus, BarChart3, Sparkles, MessageSquare } from 'lucide-react'
import Link from 'next/link'
import { CourseCard } from '@/components/CourseCard'
import { StatsOverview } from '@/components/StatsOverview'

interface Course {
  id: string
  name: string
  description: string
  subject: string
  materials_count: number
  study_sessions: number
  total_study_time: number
  created_at: string
}

export default function HomePage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const response = await fetch('http://localhost:8000/courses')
      const data = await response.json()
      setCourses(data.courses || [])
    } catch (error) {
      console.error('Errore nel caricamento dei corsi:', error)
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
          <p className="mt-4 text-gray-600 font-medium animate-pulse">Caricamento corsi...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 rounded-3xl opacity-90"></div>
        <div className="absolute inset-0 bg-[url('/hero-pattern.svg')] opacity-10"></div>

        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-10 left-10 w-20 h-20 bg-white/10 rounded-full float"></div>
          <div className="absolute top-20 right-20 w-32 h-32 bg-white/5 rounded-full float" style={{ animationDelay: '1s' }}></div>
          <div className="absolute bottom-10 left-1/3 w-16 h-16 bg-white/10 rounded-full float" style={{ animationDelay: '2s' }}></div>
          <div className="absolute top-1/3 right-10 w-24 h-24 bg-white/5 rounded-full float" style={{ animationDelay: '1.5s' }}></div>
        </div>

        <div className="relative glass rounded-3xl p-8 md:p-12 text-white">
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 space-y-4 sm:space-y-0">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl hover-lift">
                  <Sparkles className="h-8 w-8 text-yellow-300" />
                </div>
                <div className="px-4 py-2 bg-gradient-to-r from-green-400/30 to-emerald-400/30 backdrop-blur-sm rounded-full border border-white/20">
                  <span className="text-sm font-semibold flex items-center">
                    <span className="mr-2">🎓</span>
                    Piattaforma di Studio AI Avanzata
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs font-medium">Online</span>
              </div>
            </div>

            <div className="text-center mb-12">
              <h1 className="heading-1 mb-6 text-white">
                Il Tuo Tutor<br />
                <span className="bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">
                  Personale AI
                </span>
              </h1>

              <p className="body-large text-blue-100 max-w-3xl mx-auto mb-8">
                Trasforma il tuo studio universitario con l'intelligenza artificiale avanzata.
                Carica i tuoi materiali, chatta con un tutor esperto e traccia i tuoi progressi in tempo reale.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <Link
                  href="/courses/new"
                  className="btn btn-lg btn-primary group"
                >
                  <Plus className="h-5 w-5 mr-2 group-hover:rotate-90 transition-transform duration-300" />
                  Inizia Subito
                </Link>
                <Link
                  href="/chat"
                  className="btn btn-lg glass-dark text-white border-white/30 hover:bg-white/20"
                >
                  <MessageSquare className="h-5 w-5 mr-2" />
                  Prova la Chat
                </Link>
              </div>
            </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="group glass-dark rounded-2xl p-6 border border-white/20 hover-lift">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-yellow-400/20 rounded-xl">
                    <Brain className="h-6 w-6 text-yellow-300" />
                  </div>
                  <div className="badge badge-success text-green-300">Attivo</div>
                </div>
                <h3 className="font-bold text-lg mb-2 text-white">AI Tutor Intelligente</h3>
                <p className="text-sm text-blue-100 leading-relaxed">Chat avanzata con i tuoi materiali di studio</p>
              </div>

              <div className="group glass-dark rounded-2xl p-6 border border-white/20 hover-lift" style={{ animationDelay: '0.1s' }}>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-green-400/20 rounded-xl">
                    <BookOpen className="h-6 w-6 text-green-300" />
                  </div>
                  <div className="badge badge-primary text-blue-300">Smart</div>
                </div>
                <h3 className="font-bold text-lg mb-2 text-white">Gestione Materiali</h3>
                <p className="text-sm text-blue-100 leading-relaxed">Carica PDF e indicizzazione automatica</p>
              </div>

              <div className="group glass-dark rounded-2xl p-6 border border-white/20 hover-lift" style={{ animationDelay: '0.2s' }}>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-pink-400/20 rounded-xl">
                    <TrendingUp className="h-6 w-6 text-pink-300" />
                  </div>
                  <div className="badge badge-secondary text-purple-300">Analytics</div>
                </div>
                <h3 className="font-bold text-lg mb-2 text-white">Progressi Dettagliati</h3>
                <p className="text-sm text-blue-100 leading-relaxed">Tracciamento completo dell'apprendimento</p>
              </div>

              <div className="group glass-dark rounded-2xl p-6 border border-white/20 hover-lift" style={{ animationDelay: '0.3s' }}>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-orange-400/20 rounded-xl">
                    <BarChart3 className="h-6 w-6 text-orange-300" />
                  </div>
                  <div className="badge badge-warning text-orange-300">Auto</div>
                </div>
                <h3 className="font-bold text-lg mb-2 text-white">Quiz Personalizzati</h3>
                <p className="text-sm text-blue-100 leading-relaxed">Test generati automaticamente dai contenuti</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Overview */}
      <section className="slide-in-up">
        <StatsOverview courses={courses} />
      </section>

      {/* Courses Section */}
      <section className="space-y-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="heading-2 mb-2">I tuoi corsi</h2>
            <p className="text-gray-600">
              {courses.length === 0
                ? "Inizia il tuo viaggio di studio creando il primo corso"
                : `Gestisci i tuoi ${courses.length} cors${courses.length === 1 ? 'o' : 'si'}`
              }
            </p>
          </div>
          <Link
            href="/courses/new"
            className="btn btn-primary group"
          >
            <Plus className="h-5 w-5 mr-2 group-hover:rotate-90 transition-transform duration-300" />
            Nuovo Corso
          </Link>
        </div>

        {/* Courses Grid */}
        {courses.length === 0 ? (
          <div className="text-center py-16 glass rounded-3xl border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors duration-300">
            <div className="max-w-md mx-auto">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                <BookOpen className="h-10 w-10 text-gray-400" />
              </div>
              <h3 className="heading-3 mb-4">
                Nessun corso ancora creato
              </h3>
              <p className="body-medium text-gray-600 mb-8 leading-relaxed">
                Inizia creando il tuo primo corso per caricare materiali didattici e iniziare a studiare con il tuo tutor AI personalizzato.
              </p>
              <Link
                href="/courses/new"
                className="btn btn-primary btn-lg group"
              >
                <Plus className="h-5 w-5 mr-2 group-hover:rotate-90 transition-transform duration-300" />
                Crea il tuo primo corso
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid-responsive">
            {courses.map((course, index) => (
              <div
                key={course.id}
                className="slide-in-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <CourseCard course={course} onUpdate={fetchCourses} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}