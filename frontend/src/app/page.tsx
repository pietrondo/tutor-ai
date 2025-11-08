'use client'

import { useState, useEffect } from 'react'
import { BookOpen, Brain, Plus, MessageSquare, Zap, Sparkles } from 'lucide-react'
import Link from 'next/link'
import { CourseCard } from '@/components/CourseCard'
import { StatsOverview } from '@/components/StatsOverview'
import { Button } from '@/components/ui/Button'
import AIProviderBadge from '@/components/AIProviderBadge'

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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/courses`)
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
      <div className="flex justify-center items-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section - Pulito e Chiaro */}
      <section className="bg-gradient-to-br from-blue-600 to-purple-700 py-20">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="flex justify-center mb-6">
            <div className="p-3 bg-white/20 rounded-full">
              <Brain className="h-8 w-8 text-white" />
            </div>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Tutor AI Universitario
          </h1>

          <p className="text-xl text-white/90 mb-4 max-w-3xl mx-auto">
            Studia in modo intelligente con l'AI che impara dai tuoi materiali.
            Carica PDF, genera mappe concettuali e slide personalizzate.
          </p>

          <div className="flex items-center justify-center space-x-3 mb-6">
            <span className="text-white/80 text-sm">Powered by:</span>
            <AIProviderBadge showDetails={true} />
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/courses">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100 shadow-lg">
                <Plus className="h-5 w-5 mr-2" />
                Crea Corso
              </Button>
            </Link>
            <Link href="/chat">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                <MessageSquare className="h-5 w-5 mr-2" />
                Prova Chat AI
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Cards - Più semplici e chiari */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Come funziona
            </h2>
            <p className="text-lg text-gray-600">
              Strumenti intelligenti per migliorare il tuo studio
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                1. Carica Materiali
              </h3>
              <p className="text-gray-600">
                Upload dei tuoi PDF e libri di testo
              </p>
            </div>

            <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Brain className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                2. Chatta con l'AI
              </h3>
              <p className="text-gray-600">
                Fai domande sui tuoi materiali di studio
              </p>
            </div>

            <div className="text-center p-6 bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Zap className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                3. Genera Contenuti
              </h3>
              <p className="text-gray-600">
                Crea mappe concettuali e slide automaticamente
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <StatsOverview courses={courses} />
        </div>
      </section>

      {/* Courses Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                I Tuoi Corsi
              </h2>
              <p className="text-gray-600">
                {courses.length === 0
                  ? "Crea il tuo primo corso per iniziare a studiare"
                  : `Hai ${courses.length} cors${courses.length === 1 ? 'o' : 'si'} attivi`
                }
              </p>
            </div>
            <Link href="/courses/new">
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Nuovo Corso
              </Button>
            </Link>
          </div>

          {courses.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border-2 border-dashed border-gray-300">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Nessun corso ancora
              </h3>
              <p className="text-gray-600 mb-6">
                Inizia creando il tuo primo corso per caricare i materiali di studio
              </p>
              <Link href="/courses/new">
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Crea Corso
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses.map((course, index) => (
                <div
                  key={course.id}
                  className="animate-slide-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <CourseCard course={course} onUpdate={fetchCourses} />
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Pronto a trasformare il tuo studio?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Unisciti a migliaia di studenti che usano già l'AI per migliorare i loro risultati
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/courses/new">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100 shadow-lg">
                <Sparkles className="h-5 w-5 mr-2" />
                Inizia Ora
              </Button>
            </Link>
            <Link href="/chat">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                <MessageSquare className="h-5 w-5 mr-2" />
                Prova la Chat
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
