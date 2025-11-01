import { render, screen } from '@testing-library/react'
import { ChatMessage } from '../ChatMessage'

// Mock react-markdown
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }: { children: string }) {
    return <div>{children}</div>
  }
})

jest.mock('remark-gfm', () => ({}))

const mockUserMessage = {
  id: '1',
  content: 'Ciao, come stai?',
  role: 'user' as const,
  timestamp: '2024-01-01T10:30:00Z'
}

const mockAssistantMessage = {
  id: '2',
  content: 'Ciao! Sto molto bene, grazie. Come posso aiutarti oggi con i tuoi studi?',
  role: 'assistant' as const,
  timestamp: '2024-01-01T10:30:15Z'
}

const mockAssistantMessageWithSources = {
  id: '3',
  content: 'Ecco una spiegazione dettagliata dell\'argomento che hai richiesto.',
  role: 'assistant' as const,
  timestamp: '2024-01-01T10:31:00Z',
  sources: [
    {
      source: 'capitolo_1.pdf',
      chunk_index: 0,
      relevance_score: 0.95
    },
    {
      source: 'appunti_lezione.pdf',
      chunk_index: 2,
      relevance_score: 0.87
    },
    {
      source: 'esercizi_svolti.pdf',
      chunk_index: 1,
      relevance_score: 0.72
    },
    {
      source: 'libro_testo.pdf',
      chunk_index: 5,
      relevance_score: 0.65
    }
  ]
}

describe('ChatMessage', () => {
  it('renders user message correctly', () => {
    render(<ChatMessage message={mockUserMessage} />)

    expect(screen.getByText('Ciao, come stai?')).toBeInTheDocument()
    expect(screen.getByText('Tu')).toBeInTheDocument()
    expect(screen.getByText(/\d{2}:\d{2}/)).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    render(<ChatMessage message={mockAssistantMessage} />)

    expect(screen.getByText('Ciao! Sto molto bene, grazie. Come posso aiutarti oggi con i tuoi studi?')).toBeInTheDocument()
    expect(screen.getByText('Tutor AI')).toBeInTheDocument()
    expect(screen.getByText(/\d{2}:\d{2}/)).toBeInTheDocument()
  })

  it('displays user message on the right side', () => {
    const { container } = render(<ChatMessage message={mockUserMessage} />)

    const messageContainer = container.querySelector('.flex.justify-end')
    expect(messageContainer).toBeInTheDocument()
  })

  it('displays assistant message on the left side', () => {
    const { container } = render(<ChatMessage message={mockAssistantMessage} />)

    const messageContainer = container.querySelector('.flex.justify-start')
    expect(messageContainer).toBeInTheDocument()
  })

  it('shows sources when assistant message has sources', () => {
    render(<ChatMessage message={mockAssistantMessageWithSources} />)

    expect(screen.getByText('Fonti:')).toBeInTheDocument()
    expect(screen.getByText('capitolo_1.pdf')).toBeInTheDocument()
    expect(screen.getByText('appunti_lezione.pdf')).toBeInTheDocument()
    expect(screen.getByText('esercizi_svolti.pdf')).toBeInTheDocument()
    expect(screen.getByText('95%')).toBeInTheDocument()
    expect(screen.getByText('87%')).toBeInTheDocument()
    expect(screen.getByText('72%')).toBeInTheDocument()
  })

  it('shows "more sources" text when there are more than 3 sources', () => {
    render(<ChatMessage message={mockAssistantMessageWithSources} />)

    expect(screen.getByText('+1 altre fonti')).toBeInTheDocument()
  })

  it('limits sources display to 3 items', () => {
    render(<ChatMessage message={mockAssistantMessageWithSources} />)

    // Should show first 3 sources
    expect(screen.getByText('capitolo_1.pdf')).toBeInTheDocument()
    expect(screen.getByText('appunti_lezione.pdf')).toBeInTheDocument()
    expect(screen.getByText('esercizi_svolti.pdf')).toBeInTheDocument()

    // Should not show the 4th source in the main list
    expect(screen.queryByText('libro_testo.pdf')).not.toBeInTheDocument()
  })

  it('does not show sources section when no sources are provided', () => {
    render(<ChatMessage message={mockAssistantMessage} />)

    expect(screen.queryByText('Fonti:')).not.toBeInTheDocument()
  })

  it('formats time correctly', () => {
    const messageWithDifferentTime = {
      ...mockUserMessage,
      timestamp: '2024-01-01T10:45:30Z' // Use a time that will work regardless of timezone
    }

    render(<ChatMessage message={messageWithDifferentTime} />)

    expect(screen.getByText(/\d{2}:\d{2}/)).toBeInTheDocument()
  })

  it('renders markdown content correctly', () => {
    const messageWithMarkdown = {
      ...mockAssistantMessage,
      content: '**Grassetto** e *corsivo* e `codice`'
    }

    render(<ChatMessage message={messageWithMarkdown} />)

    const messageContent = screen.getByText(/Grassetto/).closest('.prose')
    expect(messageContent).toBeInTheDocument()
  })

  it('shows correct icons for user and assistant', () => {
    const { container } = render(<ChatMessage message={mockUserMessage} />)
    const userIcon = container.querySelector('.text-blue-600')
    expect(userIcon).toBeInTheDocument()

    const { container: assistantContainer } = render(<ChatMessage message={mockAssistantMessage} />)
    const assistantIcon = assistantContainer.querySelector('.text-green-600')
    expect(assistantIcon).toBeInTheDocument()
  })
})