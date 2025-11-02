'use client'

import Link from 'next/link'
import { BookOpen, Clock, FileText, MessageSquare, Trash2, Edit, Library } from 'lucide-react'
import { useState } from 'react'

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

interface CourseCardProps {
  course: Course
  onUpdate: () => void
}

export function CourseCard({ course, onUpdate }: CourseCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (!confirm(`Sei sicuro di voler eliminare il corso "${course.name}"?`)) {
      return
    }

    setIsDeleting(true)
    try {
      const response = await fetch(`http://localhost:8000/courses/${course.id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        onUpdate()
      } else {
        alert('Errore nell\'eliminazione del corso')
      }
    } catch (error) {
      console.error('Errore nell\'eliminazione del corso:', error)
      alert('Errore nell\'eliminazione del corso')
    } finally {
      setIsDeleting(false)
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

  return (
    <div className="group relative glass rounded-3xl shadow-xl hover:shadow-2xl transition-all duration-500 hover:scale-[1.03] border border-gray-200/50 overflow-hidden card-interactive">
      {/* Gradient Border Effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

      {/* Top Accent Line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>

      <div className="relative p-8">
        {/* Header with actions */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                {course.name}
              </h3>
              <div className="px-2 py-1 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full">
                <span className="text-xs font-semibold text-blue-700">{course.subject}</span>
              </div>
            </div>
            <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">{course.description || 'Nessuna descrizione disponibile'}</p>
          </div>

          <div className="flex space-x-1 ml-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <Link
              href={`/courses/${course.id}/edit`}
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200"
              title="Modifica corso"
            >
              <Edit className="h-4 w-4" />
            </Link>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200 disabled:opacity-50"
              title="Elimina corso"
            >
              {isDeleting ? (
                <div className="loading-spinner h-4 w-4"></div>
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="text-center group-hover:scale-110 transition-all duration-300">
            <div className="relative mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:shadow-xl transition-all duration-300">
                <FileText className="h-6 w-6 text-white" />
              </div>
              {course.materials_count > 0 && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
              )}
            </div>
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {course.materials_count}
            </div>
            <p className="text-xs text-gray-500 font-medium mt-1">Materiali</p>
          </div>

          <div className="text-center group-hover:scale-110 transition-all duration-300" style={{ transitionDelay: '50ms' }}>
            <div className="relative mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:shadow-xl transition-all duration-300">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              {course.study_sessions > 0 && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full animate-pulse"></div>
              )}
            </div>
            <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              {course.study_sessions}
            </div>
            <p className="text-xs text-gray-500 font-medium mt-1">Sessioni</p>
          </div>

          <div className="text-center group-hover:scale-110 transition-all duration-300" style={{ transitionDelay: '100ms' }}>
            <div className="relative mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:shadow-xl transition-all duration-300">
                <Clock className="h-6 w-6 text-white" />
              </div>
              {course.total_study_time > 0 && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-purple-500 rounded-full animate-pulse"></div>
              )}
            </div>
            <div className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              {formatStudyTime(course.total_study_time)}
            </div>
            <p className="text-xs text-gray-500 font-medium mt-1">Studio</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 gap-3">
          <Link
            href={`/courses/${course.id}`}
            className="btn btn-primary group/btn hover-lift"
          >
            <BookOpen className="h-4 w-4 mr-2 group-hover/btn:scale-110 transition-transform duration-200" />
            Apri Corso
          </Link>

          <div className="grid grid-cols-2 gap-2">
            <Link
              href={`/courses/${course.id}/books`}
              className="btn btn-secondary group/btn hover-lift text-sm"
            >
              <Library className="h-4 w-4 mr-1 group-hover/btn:scale-110 transition-transform duration-200" />
              Libri
            </Link>

            <Link
              href={`/chat?course=${course.id}`}
              className="btn btn-success group/btn hover-lift text-sm"
            >
              <MessageSquare className="h-4 w-4 mr-1 group-hover/btn:scale-110 transition-transform duration-200" />
              Chat
            </Link>
          </div>
        </div>
      </div>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
    </div>
  )
}