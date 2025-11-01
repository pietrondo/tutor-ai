import { render, screen } from '@testing-library/react'
import { Navigation } from '../Navigation'
import { usePathname } from 'next/navigation'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}))

const mockUsePathname = usePathname as jest.MockedFunction<typeof usePathname>

describe('Navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders navigation logo correctly', () => {
    mockUsePathname.mockReturnValue('/')
    render(<Navigation />)

    expect(screen.getByAltText('Tutor AI')).toBeInTheDocument()
    expect(screen.getByText('Tutor AI')).toBeInTheDocument()
  })

  it('renders all navigation items', () => {
    mockUsePathname.mockReturnValue('/')
    render(<Navigation />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Corsi')).toBeInTheDocument()
    expect(screen.getByText('Chat Tutor')).toBeInTheDocument()
    expect(screen.getByText('Progressi')).toBeInTheDocument()
    expect(screen.getByText('Impostazioni')).toBeInTheDocument()
  })

  it('highlights active navigation item', () => {
    mockUsePathname.mockReturnValue('/courses')
    render(<Navigation />)

    const coursesLink = screen.getByText('Corsi').closest('a')
    expect(coursesLink).toHaveClass('bg-gradient-to-r')
    expect(coursesLink).toHaveClass('text-white')
  })

  it('shows AI Tutor Online status', () => {
    mockUsePathname.mockReturnValue('/')
    render(<Navigation />)

    expect(screen.getByText('AI Tutor Online')).toBeInTheDocument()

    const statusIndicator = document.querySelector('.bg-green-500')
    expect(statusIndicator).toBeInTheDocument()
  })

  it('does not highlight inactive navigation item', () => {
    mockUsePathname.mockReturnValue('/courses')
    render(<Navigation />)

    const homeLink = screen.getByText('Home').closest('a')
    expect(homeLink).not.toHaveClass('bg-gradient-to-r')
    expect(homeLink).toHaveClass('text-gray-600')
  })

  it('renders correct navigation links', () => {
    mockUsePathname.mockReturnValue('/')
    render(<Navigation />)

    const homeLink = screen.getByText('Home').closest('a')
    const coursesLink = screen.getByText('Corsi').closest('a')
    const chatLink = screen.getByText('Chat Tutor').closest('a')

    expect(homeLink).toHaveAttribute('href', '/')
    expect(coursesLink).toHaveAttribute('href', '/courses')
    expect(chatLink).toHaveAttribute('href', '/chat')
  })

  it('shows correct active state for different routes', () => {
    const routes = [
      { pathname: '/', activeText: 'Home' },
      { pathname: '/courses', activeText: 'Corsi' },
      { pathname: '/chat', activeText: 'Chat Tutor' },
      { pathname: '/progress', activeText: 'Progressi' },
      { pathname: '/settings', activeText: 'Impostazioni' },
    ]

    routes.forEach(({ pathname, activeText }) => {
      mockUsePathname.mockReturnValue(pathname)
      const { container } = render(<Navigation />)

      const activeLink = screen.getByText(activeText).closest('a')
      expect(activeLink).toHaveClass('bg-gradient-to-r')
      expect(activeLink).toHaveClass('text-white')

      container.remove()
    })
  })

  it('logo links to home page', () => {
    mockUsePathname.mockReturnValue('/courses')
    render(<Navigation />)

    const logoLink = screen.getByAltText('Tutor AI').closest('a')
    expect(logoLink).toHaveAttribute('href', '/')
  })

  it('has proper navigation structure', () => {
    mockUsePathname.mockReturnValue('/')
    const { container } = render(<Navigation />)

    const nav = container.querySelector('nav')
    expect(nav).toBeInTheDocument()
    expect(nav).toHaveClass('bg-white')
    expect(nav).toHaveClass('shadow-sm')
    expect(nav).toHaveClass('border-b')
  })

  it('shows sparkles icon near logo', () => {
    mockUsePathname.mockReturnValue('/')
    const { container } = render(<Navigation />)

    const sparklesIcon = container.querySelector('.text-yellow-500')
    expect(sparklesIcon).toBeInTheDocument()
    expect(sparklesIcon).toHaveClass('animate-pulse')
  })
})