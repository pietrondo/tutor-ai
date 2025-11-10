import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import BookDetailClient from '../BookDetailClient'
import CoursesMindmapPage from '@/app/courses/[id]/books/[bookId]/mindmap/page'
import BookDetailMindmapPage from '@/app/book-detail/[courseId]/[bookId]/mindmap/page'
import { fetchFromBackend } from '@/lib/api'

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
    refresh: jest.fn(),
  }),
}))

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: { children: ReactNode; href: string }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  )
})

jest.mock('@/components/books/mindmap/MindmapClient', () => ({
  __esModule: true,
  default: jest.fn(({ courseId, bookId }) => (
    <div data-testid="mocked-mindmap-client" data-course-id={courseId} data-book-id={bookId}>
      mocked mindmap
    </div>
  )),
}))

jest.mock('@/lib/api', () => ({
  fetchFromBackend: jest.fn(),
}))

const mockBookPayload = {
  book: {
    id: 'book-456',
    title: 'Mindmap Ready',
    author: 'Test Author',
    isbn: '1234567890',
    description: 'Test description',
    year: '2024',
    publisher: 'Test Publisher',
    materials_count: 1,
    study_sessions: 0,
    total_study_time: 0,
    created_at: '2024-01-01T00:00:00Z',
    chapters: [],
    tags: [],
    materials: [
      {
        filename: 'chapter-1.pdf',
        size: 1024,
        uploaded_at: '2024-01-02T00:00:00Z',
        file_path: '/uploads/chapter-1.pdf',
      },
    ],
  },
}

const mockCoursePayload = {
  course: {
    id: 'course-123',
    name: 'Mindmap Course',
  },
}

const fetchFromBackendMock = fetchFromBackend as jest.MockedFunction<typeof fetchFromBackend>

const mockApiResponse = <T,>(payload: T) =>
  Promise.resolve({
    ok: true,
    json: async () => payload,
  } as Response)

describe('Mindmap links and routes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    fetchFromBackendMock.mockImplementation(url => {
      if (url.includes('/books/')) {
        return mockApiResponse(mockBookPayload)
      }
      if (/\/courses\/[^/]+$/.test(url)) {
        return mockApiResponse(mockCoursePayload)
      }
      return Promise.resolve({
        ok: false,
        json: async () => ({}),
      } as Response)
    })
  })

  it('renders the quick action link to the courses mindmap route', async () => {
    render(<BookDetailClient courseId="course-123" bookId="book-456" />)

    const mindmapLink = await screen.findByRole('link', { name: /Mappa Concettuale/i })
    expect(mindmapLink).toHaveAttribute('href', '/courses/course-123/books/book-456/mindmap')
  })

  it('courses mindmap page forwards params to the client', async () => {
    const element = await CoursesMindmapPage({ params: { id: 'course-999', bookId: 'book-888' } })
    render(element)

    const client = screen.getByTestId('mocked-mindmap-client')
    expect(client).toHaveAttribute('data-course-id', 'course-999')
    expect(client).toHaveAttribute('data-book-id', 'book-888')
  })

  it('book-detail mindmap page forwards params to the client', async () => {
    const element = await BookDetailMindmapPage({ params: { courseId: 'course-777', bookId: 'book-666' } })
    render(element)

    const client = screen.getByTestId('mocked-mindmap-client')
    expect(client).toHaveAttribute('data-course-id', 'course-777')
    expect(client).toHaveAttribute('data-book-id', 'book-666')
  })
})
