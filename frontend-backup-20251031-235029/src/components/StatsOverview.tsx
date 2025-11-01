'use client'

import { BookOpen, Clock, TrendingUp, Target } from 'lucide-react'

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

interface StatsOverviewProps {
  courses: Course[]
}

export function StatsOverview({ courses }: StatsOverviewProps) {
  const totalCourses = courses.length
  const totalMaterials = courses.reduce((sum, course) => sum + course.materials_count, 0)
  const totalSessions = courses.reduce((sum, course) => sum + course.study_sessions, 0)
  const totalStudyTime = courses.reduce((sum, course) => sum + course.total_study_time, 0)

  const formatStudyTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h ${mins}m`
    }
    return `${mins}m`
  }

  const stats = [
    {
      label: 'Corsi Attivi',
      value: totalCourses.toString(),
      icon: BookOpen,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      label: 'Materiali Caricati',
      value: totalMaterials.toString(),
      icon: Target,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      label: 'Sessioni di Studio',
      value: totalSessions.toString(),
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    {
      label: 'Tempo Totale',
      value: formatStudyTime(totalStudyTime),
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <div key={index} className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
            <div className={`p-3 rounded-lg ${stat.bgColor}`}>
              <stat.icon className={`h-6 w-6 ${stat.color}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}