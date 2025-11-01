import { render, screen, waitFor } from '@testing-library/react'
import HomePage from '../page'

// Mock fetch
global.fetch = jest.fn()

// Mock CourseCard and StatsOverview components
jest.mock('../../components/CourseCard', () => ({
  CourseCard: ({ course, onUpdate }: { course: any; onUpdate: () => void }) => (
    <div data-testid="course-card" onClick={onUpdate}>
      {course.name}
    </div>
  )
}))

jest.mock('../../components/StatsOverview', () => ({
  StatsOverview: ({ courses }: { courses: any[] }) => (
    <div data-testid="stats-overview">
      Stats for {courses.length} courses
    </div>
  )
}))

const mockCourses = [
  {
    id: '1',
    name: 'Matematica Avanzata',
    description: 'Corso di calcolo differenziale',
    subject: 'Matematica',
    materials_count: 10,
    study_sessions: 5,
    total_study_time: 120,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    name: 'Fisica Quantistica',
    description: 'Introduzione alla meccanica quantistica',
    subject: 'Fisica',
    materials_count: 8,
    study_sessions: 3,
    total_study_time: 90,
    created_at: '2024-01-02T00:00:00Z'
  }
]

describe('HomePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows loading state initially', () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(<HomePage />)

    const loadingSpinner = document.querySelector('.animate-spin')
    expect(loadingSpinner).toBeInTheDocument()
  })

  it('renders hero section correctly', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Il Tuo Tutor/)).toBeInTheDocument()
      expect(screen.getByText(/Personale AI/)).toBeInTheDocument()
      expect(screen.getByText('Inizia Subito')).toBeInTheDocument()
      expect(screen.getByText('Prova la Chat')).toBeInTheDocument()
    })
  })

  it('renders feature cards correctly', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('AI Tutor Intelligente')).toBeInTheDocument()
      expect(screen.getByText('Gestione Materiali')).toBeInTheDocument()
      expect(screen.getByText('Progressi Dettagliati')).toBeInTheDocument()
      expect(screen.getByText('Quiz Personalizzati')).toBeInTheDocument()
    })
  })

  it('displays courses when data is loaded', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: mockCourses })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('I tuoi corsi')).toBeInTheDocument()
      expect(screen.getByTestId('stats-overview')).toBeInTheDocument()
      expect(screen.getByTestId('stats-overview')).toHaveTextContent('Stats for 2 courses')
    })

    const courseCards = screen.getAllByTestId('course-card')
    expect(courseCards).toHaveLength(2)
    expect(courseCards[0]).toHaveTextContent('Matematica Avanzata')
    expect(courseCards[1]).toHaveTextContent('Fisica Quantistica')
  })

  it('shows empty state when no courses exist', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Nessun corso ancora creato')).toBeInTheDocument()
      expect(screen.getByText('Inizia creando il tuo primo corso per caricare materiali e iniziare a studiare')).toBeInTheDocument()
      expect(screen.getByText('Crea il tuo primo corso')).toBeInTheDocument()
    })
  })

  it('fetches courses on component mount', () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/courses')
  })

  it('shows new course buttons in both hero and main section', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      const newCourseButtons = screen.getAllByText('Nuovo Corso')
      expect(newCourseButtons.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('has correct navigation links', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      const startsNowLink = screen.getByText('Inizia Subito').closest('a')
      const tryChatLink = screen.getByText('Prova la Chat').closest('a')
      const newCourseLink = screen.getByText('Crea il tuo primo corso').closest('a')

      expect(startsNowLink).toHaveAttribute('href', '/courses/new')
      expect(tryChatLink).toHaveAttribute('href', '/chat')
      expect(newCourseLink).toHaveAttribute('href', '/courses/new')
    })
  })

  it('displays platform tagline', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ courses: [] })
    } as Response)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('🎓 Piattaforma di Studio AI Avanzata')).toBeInTheDocument()
    })
  })

  it('handles fetch errors gracefully', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    render(<HomePage />)

    await waitFor(() => {
      // Should still render the page without crashing
      expect(screen.getByText('I tuoi corsi')).toBeInTheDocument()
    })
  })
})