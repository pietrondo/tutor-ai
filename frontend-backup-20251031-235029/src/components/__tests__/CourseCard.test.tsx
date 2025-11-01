import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CourseCard } from '../CourseCard'
import { useRouter } from 'next/router'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}))

// Mock fetch
global.fetch = jest.fn()

const mockCourse = {
  id: '1',
  name: 'Matematica Avanzata',
  description: 'Corso di matematica avanzata con focus su calcolo differenziale e integrale',
  subject: 'Matematica',
  materials_count: 15,
  study_sessions: 8,
  total_study_time: 240,
  created_at: '2024-01-01T00:00:00Z'
}

const mockOnUpdate = jest.fn()

describe('CourseCard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock confirm to return true by default
    window.confirm = jest.fn(() => true)
    // Mock alert
    window.alert = jest.fn()
  })

  it('renders course information correctly', () => {
    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    expect(screen.getByText('Matematica Avanzata')).toBeInTheDocument()
    expect(screen.getByText('Matematica')).toBeInTheDocument()
    expect(screen.getByText('Corso di matematica avanzata con focus su calcolo differenziale e integrale')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('4h 0m')).toBeInTheDocument()
  })

  it('displays correct labels for stats', () => {
    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    expect(screen.getByText('Materiali')).toBeInTheDocument()
    expect(screen.getByText('Sessioni')).toBeInTheDocument()
    expect(screen.getByText('Studio')).toBeInTheDocument()
  })

  it('shows edit and delete buttons on hover', () => {
    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    const container = screen.getByText('Matematica Avanzata').closest('[class*="group"]')
    fireEvent.mouseEnter(container!)

    expect(screen.getByTitle('Modifica corso')).toBeInTheDocument()
    expect(screen.getByTitle('Elimina corso')).toBeInTheDocument()
  })

  it('calls delete API when delete button is clicked', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
    } as Response)

    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    const container = screen.getByText('Matematica Avanzata').closest('[class*="group"]')
    fireEvent.mouseEnter(container!)

    const deleteButton = screen.getByTitle('Elimina corso')
    fireEvent.click(deleteButton)

    expect(window.confirm).toHaveBeenCalledWith('Sei sicuro di voler eliminare il corso "Matematica Avanzata"?')
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/courses/1',
      { method: 'DELETE' }
    )

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled()
    })
  })

  it('shows error alert when delete fails', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    } as Response)

    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    const container = screen.getByText('Matematica Avanzata').closest('[class*="group"]')
    fireEvent.mouseEnter(container!)

    const deleteButton = screen.getByTitle('Elimina corso')
    fireEvent.click(deleteButton)

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Errore nell\'eliminazione del corso')
    })
  })

  it('does not delete when user cancels confirmation', async () => {
    window.confirm = jest.fn(() => false)
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    const container = screen.getByText('Matematica Avanzata').closest('[class*="group"]')
    fireEvent.mouseEnter(container!)

    const deleteButton = screen.getByTitle('Elimina corso')
    fireEvent.click(deleteButton)

    expect(mockFetch).not.toHaveBeenCalled()
    expect(mockOnUpdate).not.toHaveBeenCalled()
  })

  it('shows loading state during deletion', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ ok: true } as Response), 100)))

    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    const container = screen.getByText('Matematica Avanzata').closest('[class*="group"]')
    fireEvent.mouseEnter(container!)

    const deleteButton = screen.getByTitle('Elimina corso')
    fireEvent.click(deleteButton)

    // Check if button is disabled
    expect(deleteButton).toBeDisabled()

    // Wait for deletion to complete
    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled()
    })
  })

  it('has correct links for course and chat', () => {
    render(<CourseCard course={mockCourse} onUpdate={mockOnUpdate} />)

    const openCourseButton = screen.getByText('Apri Corso')
    const chatTutorButton = screen.getByText('Chat Tutor')

    expect(openCourseButton.closest('a')).toHaveAttribute('href', '/courses/1')
    expect(chatTutorButton.closest('a')).toHaveAttribute('href', '/chat?course=1')
  })

  it('formats study time correctly for different values', () => {
    const courseWithMinutes = {
      ...mockCourse,
      total_study_time: 45
    }

    render(<CourseCard course={courseWithMinutes} onUpdate={mockOnUpdate} />)
    expect(screen.getByText('45m')).toBeInTheDocument()
  })

  it('formats study time correctly for hours and minutes', () => {
    const courseWithHours = {
      ...mockCourse,
      total_study_time: 125 // 2h 5m
    }

    render(<CourseCard course={courseWithHours} onUpdate={mockOnUpdate} />)
    expect(screen.getByText('2h 5m')).toBeInTheDocument()
  })
})