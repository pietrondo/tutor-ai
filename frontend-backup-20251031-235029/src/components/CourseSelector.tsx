'use client'

import { BookOpen, ChevronDown } from 'lucide-react'

interface Course {
  id: string
  name: string
  subject: string
  materials_count: number
}

interface CourseSelectorProps {
  courses: Course[]
  selectedCourse: string
  onCourseChange: (courseId: string) => void
}

export function CourseSelector({ courses, selectedCourse, onCourseChange }: CourseSelectorProps) {
  return (
    <div className="flex items-center space-x-4">
      <label htmlFor="course-select" className="form-label mb-0">
        Corso:
      </label>
      <div className="relative flex-1 max-w-md">
        <select
          id="course-select"
          value={selectedCourse}
          onChange={(e) => onCourseChange(e.target.value)}
          className="form-input appearance-none pr-10"
        >
          <option value="">Seleziona un corso...</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.name} - {course.subject}
            </option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <ChevronDown className="h-5 w-5 text-gray-400" />
        </div>
      </div>
    </div>
  )
}