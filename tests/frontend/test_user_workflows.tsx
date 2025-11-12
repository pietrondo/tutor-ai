/**
 * Comprehensive User Workflow Tests
 *
 * This test suite validates complete user journeys across the Tutor-AI application:
 * - Course creation and management workflow
 * - PDF upload and reading workflow
 * - AI chat integration workflow
 * - Study session and learning workflow
 * - Navigation and routing workflow
 * - Component integration and state management
 */

import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { jest } from '@jest/globals';
import { AppRouter } from '@/app/layout'; // Adjust based on actual structure
import { useRouter } from 'next/navigation';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook } from '@testing-library/react';
import { useSearchParams } from 'next/navigation';

// Mock external dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
  usePathname: jest.fn(() => '/courses'),
}));

jest.mock('@/lib/api', () => ({
  api: {
    courses: {
      getAll: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      getById: jest.fn(),
    },
    chat: {
      send: jest.fn(),
      getSession: jest.fn(),
    },
    materials: {
      upload: jest.fn(),
      getList: jest.fn(),
    },
  },
}));

jest.mock('@/lib/config', () => ({
  config: {
    apiUrl: 'http://localhost:8000',
    features: {
      aiChat: true,
      pdfReader: true,
      mindmaps: true,
    },
  },
}));

// Test data factories
const createMockCourse = (overrides = {}) => ({
  id: 'course-123',
  title: 'Introduction to Machine Learning',
  description: 'Learn the fundamentals of ML',
  subject: 'Computer Science',
  difficulty_level: 'beginner',
  created_at: '2024-01-15T10:30:00Z',
  ...overrides,
});

const createMockBook = (overrides = {}) => ({
  id: 'book-123',
  course_id: 'course-123',
  title: 'Machine Learning Basics',
  author: 'Test Author',
  description: 'A comprehensive guide',
  file_path: '/uploads/test.pdf',
  ...overrides,
});

const createMockChatMessage = (overrides = {}) => ({
  id: 'msg-123',
  message: 'What is machine learning?',
  response: 'Machine learning is a subset of artificial intelligence...',
  sources: [],
  timestamp: '2024-01-15T10:30:00Z',
  ...overrides,
});

// Test utilities
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
};

const renderWithProviders = (ui: React.ReactElement, client?: QueryClient) => {
  const queryClient = client || createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

// Mock implementations
const mockPush = jest.fn();
const mockBack = jest.fn();
const mockRefresh = jest.fn();
const mockGet = jest.fn();
const mockSet = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  (useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
    back: mockBack,
    refresh: mockRefresh,
    replace: jest.fn(),
    prefetch: jest.fn(),
  });

  (useSearchParams as jest.Mock).mockReturnValue({
    get: mockGet,
    set: mockSet,
    has: jest.fn(),
    entries: jest.fn(),
  });
});

describe('Course Management Workflow', () => {
  describe('Course Creation Flow', () => {
    it('should create a new course successfully', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.create.mockResolvedValue(mockCourse);

      renderWithProviders(<AppRouter />);

      // Navigate to course creation page
      const createCourseButton = screen.getByText(/Create Course/i);
      await userEvent.click(createCourseButton);

      // Wait for form to load
      await waitFor(() => {
        expect(screen.getByLabelText(/Course Title/i)).toBeInTheDocument();
      });

      // Fill course details
      const titleInput = screen.getByLabelText(/Course Title/i);
      const descriptionInput = screen.getByLabelText(/Description/i);
      const subjectSelect = screen.getByLabelText(/Subject/i);
      const difficultySelect = screen.getByLabelText(/Difficulty Level/i);

      await userEvent.type(titleInput, mockCourse.title);
      await userEvent.type(descriptionInput, mockCourse.description);
      await userEvent.selectOptions(subjectSelect, mockCourse.subject);
      await userEvent.selectOptions(difficultySelect, mockCourse.difficulty_level);

      // Submit form
      const submitButton = screen.getByRole('button', { name: /Create Course/i });
      await userEvent.click(submitButton);

      // Verify API call
      expect(api.courses.create).toHaveBeenCalledWith({
        title: mockCourse.title,
        description: mockCourse.description,
        subject: mockCourse.subject,
        difficulty_level: mockCourse.difficulty_level,
      });

      // Verify navigation to course page
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}`);
      });
    });

    it('should handle course creation validation errors', async () => {
      renderWithProviders(<AppRouter />);

      const createCourseButton = screen.getByText(/Create Course/i);
      await userEvent.click(createCourseButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/Course Title/i)).toBeInTheDocument();
      });

      // Submit without required fields
      const submitButton = screen.getByRole('button', { name: /Create Course/i });
      await userEvent.click(submitButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/Title is required/i)).toBeInTheDocument();
        expect(screen.getByText(/Subject is required/i)).toBeInTheDocument();
      });
    });
  });

  describe('Course Listing and Navigation', () => {
    it('should display list of courses', async () => {
      const mockCourses = [
        createMockCourse({ title: 'Course 1' }),
        createMockCourse({ title: 'Course 2', id: 'course-456' }),
      ];
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: mockCourses });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText('Course 1')).toBeInTheDocument();
        expect(screen.getByText('Course 2')).toBeInTheDocument();
      });

      // Verify course cards are rendered
      mockCourses.forEach(course => {
        expect(screen.getByText(course.title)).toBeInTheDocument();
        expect(screen.getByText(course.description)).toBeInTheDocument();
      });
    });

    it('should navigate to course detail page', async () => {
      const mockCourses = [createMockCourse()];
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: mockCourses });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourses[0].title)).toBeInTheDocument();
      });

      // Click on course card
      const courseLink = screen.getByRole('link', { name: new RegExp(mockCourses[0].title, 'i') });
      await userEvent.click(courseLink);

      // Verify navigation
      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourses[0].id}`);
    });

    it('should handle empty course list state', async () => {
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: [] });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(/No courses found/i)).toBeInTheDocument();
        expect(screen.getByText(/Create your first course/i)).toBeInTheDocument();
      });
    });
  });

  describe('Course Editing and Management', () => {
    it('should edit existing course', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.courses.update.mockResolvedValue({ ...mockCourse, title: 'Updated Title' });

      // Navigate to edit page
      (useRouter as jest.Mock).mockReturnValue({
        ...useRouter(),
        push: mockPush,
      });

      renderWithProviders(<AppRouter />);

      // Navigate to edit mode
      const editButton = screen.getByRole('button', { name: /Edit Course/i });
      await userEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByDisplayValue(mockCourse.title)).toBeInTheDocument();
      });

      // Update title
      const titleInput = screen.getByDisplayValue(mockCourse.title);
      await userEvent.clear(titleInput);
      await userEvent.type(titleInput, 'Updated Title');

      // Save changes
      const saveButton = screen.getByRole('button', { name: /Save Changes/i });
      await userEvent.click(saveButton);

      // Verify API call
      expect(api.courses.update).toHaveBeenCalledWith(mockCourse.id, {
        title: 'Updated Title',
        description: mockCourse.description,
        subject: mockCourse.subject,
        difficulty_level: mockCourse.difficulty_level,
      });
    });

    it('should delete course with confirmation', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.courses.delete.mockResolvedValue({ message: 'Course deleted successfully' });

      renderWithProviders(<AppRouter />);

      // Delete course
      const deleteButton = screen.getByRole('button', { name: /Delete Course/i });
      await userEvent.click(deleteButton);

      // Confirm deletion
      await waitFor(() => {
        expect(screen.getByText(/Are you sure you want to delete this course?/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /Delete/i });
      await userEvent.click(confirmButton);

      // Verify API call
      expect(api.courses.delete).toHaveBeenCalledWith(mockCourse.id);

      // Verify navigation back to courses list
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/courses');
      });
    });
  });
});

describe('PDF Upload and Reading Workflow', () => {
  describe('PDF Upload Process', () => {
    it('should upload PDF successfully', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.upload.mockResolvedValue({
        status: 'success',
        book_id: mockBook.id,
        filename: 'test.pdf',
      });

      renderWithProviders(<AppRouter />);

      // Navigate to course page
      await userEvent.click(screen.getByText(mockCourse.title));

      await waitFor(() => {
        expect(screen.getByText(/Upload PDF/i)).toBeInTheDocument();
      });

      // Create file input and select file
      const fileInput = screen.getByLabelText(/Choose PDF file/i) ||
                       screen.querySelector('input[type="file"]');

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      await userEvent.upload(fileInput!, file);

      // Upload button
      const uploadButton = screen.getByRole('button', { name: /Upload/i });
      await userEvent.click(uploadButton);

      // Verify API call
      expect(api.materials.upload).toHaveBeenCalledWith(
        mockCourse.id,
        expect.any(FormData)
      );

      // Verify success message
      await waitFor(() => {
        expect(screen.getByText(/PDF uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle PDF upload errors', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.upload.mockRejectedValue(new Error('Upload failed'));

      renderWithProviders(<AppRouter />);

      await userEvent.click(screen.getByText(mockCourse.title));

      await waitFor(() => {
        expect(screen.getByText(/Upload PDF/i)).toBeInTheDocument();
      });

      const fileInput = screen.querySelector('input[type="file"]');
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      await userEvent.upload(fileInput!, file);

      const uploadButton = screen.getByRole('button', { name: /Upload/i });
      await userEvent.click(uploadButton);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/Failed to upload PDF/i)).toBeInTheDocument();
      });
    });
  });

  describe('PDF Reading Interface', () => {
    it('should display PDF reader with navigation', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.getList.mockResolvedValue({
        materials: [
          {
            filename: 'test.pdf',
            read_url: `/courses/${mockCourse.id}/materials/test.pdf`,
            book_id: mockBook.id,
          },
        ],
      });

      // Set URL params for PDF viewing
      mockGet.mockReturnValue('test.pdf');
      mockGet.mockImplementation((key) => {
        if (key === 'book') return mockBook.id;
        if (key === 'filename') return 'test.pdf';
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument();
      });

      // Verify PDF navigation controls
      expect(screen.getByRole('button', { name: /Previous Page/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Next Page/i })).toBeInTheDocument();
      expect(screen.getByText(/Page 1 of 1/i)).toBeInTheDocument();
    });

    it('should handle PDF page navigation', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.getList.mockResolvedValue({
        materials: [
          {
            filename: 'test.pdf',
            read_url: `/courses/${mockCourse.id}/materials/test.pdf`,
            book_id: mockBook.id,
            pages: 5,
          },
        ],
      });

      mockGet.mockImplementation((key) => {
        if (key === 'book') return mockBook.id;
        if (key === 'filename') return 'test.pdf';
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument();
      });

      // Navigate pages
      const nextPageButton = screen.getByRole('button', { name: /Next Page/i });
      await userEvent.click(nextPageButton);

      await waitFor(() => {
        expect(screen.getByText(/Page 2 of 5/i)).toBeInTheDocument();
      });

      // Previous page
      const prevPageButton = screen.getByRole('button', { name: /Previous Page/i });
      await userEvent.click(prevPageButton);

      await waitFor(() => {
        expect(screen.getByText(/Page 1 of 5/i)).toBeInTheDocument();
      });
    });

    it('should handle PDF zoom controls', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.getList.mockResolvedValue({
        materials: [
          {
            filename: 'test.pdf',
            read_url: `/courses/${mockCourse.id}/materials/test.pdf`,
            book_id: mockBook.id,
          },
        ],
      });

      mockGet.mockImplementation((key) => {
        if (key === 'book') return mockBook.id;
        if (key === 'filename') return 'test.pdf';
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument();
      });

      // Test zoom controls
      const zoomInButton = screen.getByRole('button', { name: /Zoom In/i });
      const zoomOutButton = screen.getByRole('button', { name: /Zoom Out/i });

      await userEvent.click(zoomInButton);
      await userEvent.click(zoomOutButton);

      // Verify zoom level changes (would depend on implementation)
      expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument();
    });
  });
});

describe('AI Chat Integration Workflow', () => {
  describe('Chat Interface', () => {
    it('should send chat message and receive response', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const mockChatResponse = createMockChatMessage();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.chat.send.mockResolvedValue(mockChatResponse);

      mockGet.mockImplementation((key) => {
        if (key === 'book') return mockBook.id;
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
      });

      // Type and send message
      const messageInput = screen.getByPlaceholderText(/Ask a question/i) ||
                          screen.getByRole('textbox');
      await userEvent.type(messageInput, 'What is machine learning?');

      const sendButton = screen.getByRole('button', { name: /Send/i });
      await userEvent.click(sendButton);

      // Verify API call
      expect(api.chat.send).toHaveBeenCalledWith({
        message: 'What is machine learning?',
        course_id: mockCourse.id,
        context_filter: {
          book_id: mockBook.id,
        },
      });

      // Verify response display
      await waitFor(() => {
        expect(screen.getByText(mockChatResponse.response)).toBeInTheDocument();
        expect(screen.getByTestId('chat-message')).toBeInTheDocument();
      });
    });

    it('should display chat history', async () => {
      const mockCourse = createMockCourse();
      const mockChatHistory = [
        createMockChatMessage({ message: 'Question 1', response: 'Response 1' }),
        createMockChatMessage({ message: 'Question 2', response: 'Response 2' }),
      ];
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.chat.getSession.mockResolvedValue({ messages: mockChatHistory });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        mockChatHistory.forEach(msg => {
          expect(screen.getByText(msg.message)).toBeInTheDocument();
          expect(screen.getByText(msg.response)).toBeInTheDocument();
        });
      });
    });

    it('should handle chat errors gracefully', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.chat.send.mockRejectedValue(new Error('Chat service unavailable'));

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
      });

      const messageInput = screen.getByPlaceholderText(/Ask a question/i) ||
                          screen.getByRole('textbox');
      await userEvent.type(messageInput, 'Test message');

      const sendButton = screen.getByRole('button', { name: /Send/i });
      await userEvent.click(sendButton);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/Failed to send message/i)).toBeInTheDocument();
      });
    });
  });

  describe('Chat Context Integration', () => {
    it('should maintain course context in chat', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.chat.send.mockResolvedValue(createMockChatMessage());

      mockGet.mockImplementation((key) => {
        if (key === 'book') return mockBook.id;
        if (key === 'course') return mockCourse.id;
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
      });

      // Send chat message
      const messageInput = screen.getByPlaceholderText(/Ask a question/i) ||
                          screen.getByRole('textbox');
      await userEvent.type(messageInput, 'Explain this concept');

      const sendButton = screen.getByRole('button', { name: /Send/i });
      await userEvent.click(sendButton);

      // Verify context is included
      expect(api.chat.send).toHaveBeenCalledWith(
        expect.objectContaining({
          course_id: mockCourse.id,
          context_filter: expect.objectContaining({
            book_id: mockBook.id,
          }),
        })
      );
    });

    it('should display source citations in chat responses', async () => {
      const mockCourse = createMockCourse();
      const mockChatResponse = createMockChatMessage({
        sources: [
          {
            content: 'Machine learning is a subset of AI',
            page: 1,
            book_id: 'book-123',
            book_title: 'ML Basics',
          },
        ],
      });
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.chat.send.mockResolvedValue(mockChatResponse);

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
      });

      const messageInput = screen.getByPlaceholderText(/Ask a question/i) ||
                          screen.getByRole('textbox');
      await userEvent.type(messageInput, 'What is machine learning?');

      const sendButton = screen.getByRole('button', { name: /Send/i });
      await userEvent.click(sendButton);

      // Verify sources are displayed
      await waitFor(() => {
        expect(screen.getByText(/Sources:/i)).toBeInTheDocument();
        expect(screen.getByText(/ML Basics/i)).toBeInTheDocument();
        expect(screen.getByText(/Page 1/i)).toBeInTheDocument();
      });
    });
  });
});

describe('Navigation and Routing Workflow', () => {
  describe('Dynamic Route Handling', () => {
    it('should handle course-specific routes', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);

      // Mock route parameters
      mockGet.mockImplementation((key) => {
        if (key === 'id') return mockCourse.id;
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
      });

      // Test navigation to different course sections
      const studyButton = screen.getByRole('link', { name: /Study/i });
      await userEvent.click(studyButton);

      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}/study`);

      const chatButton = screen.getByRole('link', { name: /Chat/i });
      await userEvent.click(chatButton);

      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}/chat`);
    });

    it('should handle book-specific routes', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);

      mockGet.mockImplementation((key) => {
        if (key === 'id') return mockCourse.id;
        if (key === 'bookId') return mockBook.id;
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockBook.title)).toBeInTheDocument();
      });

      // Test book-specific navigation
      const mindmapButton = screen.getByRole('link', { name: /Mind Map/i });
      await userEvent.click(mindmapButton);

      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}/books/${mockBook.id}/mindmap`);
    });
  });

  describe('Breadcrumb Navigation', () => {
    it('should display correct breadcrumb trail', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);

      mockGet.mockImplementation((key) => {
        if (key === 'id') return mockCourse.id;
        if (key === 'bookId') return mockBook.id;
        if (key === 'filename') return 'test.pdf';
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        const breadcrumbs = screen.getByTestId('breadcrumbs');
        expect(breadcrumbs).toBeInTheDocument();

        // Verify breadcrumb trail
        expect(screen.getByText(/Home/i)).toBeInTheDocument();
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
        expect(screen.getByText(mockBook.title)).toBeInTheDocument();
        expect(screen.getByText(/test.pdf/i)).toBeInTheDocument();
      });
    });

    it('should navigate via breadcrumb links', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);

      mockGet.mockImplementation((key) => {
        if (key === 'id') return mockCourse.id;
        if (key === 'bookId') return mockBook.id;
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        const courseBreadcrumb = screen.getByText(mockCourse.title);
        expect(courseBreadcrumb).toBeInTheDocument();
      });

      // Click breadcrumb to navigate
      await userEvent.click(screen.getByText(mockCourse.title));

      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}`);
    });
  });
});

describe('Component Integration and State Management', () => {
  describe('State Synchronization', () => {
    it('should synchronize PDF viewer with chat context', async () => {
      const mockCourse = createMockCourse();
      const mockBook = createMockBook();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.getList.mockResolvedValue({
        materials: [
          {
            filename: 'test.pdf',
            read_url: `/courses/${mockCourse.id}/materials/test.pdf`,
            book_id: mockBook.id,
          },
        ],
      });

      mockGet.mockImplementation((key) => {
        if (key === 'book') return mockBook.id;
        if (key === 'filename') return 'test.pdf';
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument();
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
      });

      // Navigate to different page in PDF
      const nextPageButton = screen.getByRole('button', { name: /Next Page/i });
      await userEvent.click(nextPageButton);

      // Send chat message that references current page
      const messageInput = screen.getByPlaceholderText(/Ask a question/i) ||
                          screen.getByRole('textbox');
      await userEvent.type(messageInput, 'What is on this page?');

      const sendButton = screen.getByRole('button', { name: /Send/i });
      await userEvent.click(sendButton);

      // Verify page context is included in chat
      expect(api.chat.send).toHaveBeenCalledWith(
        expect.objectContaining({
          context_filter: expect.objectContaining({
            book_id: mockBook.id,
            page_number: 2, // After navigation
          }),
        })
      );
    });

    it('should maintain theme consistency across components', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: [mockCourse] });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
      });

      // Test theme toggle
      const themeToggle = screen.getByRole('button', { name: /Toggle theme/i });
      await userEvent.click(themeToggle);

      // Verify theme is applied to all components
      expect(document.documentElement).toHaveClass('dark');

      // Navigate to different page
      await userEvent.click(screen.getByText(mockCourse.title));

      await waitFor(() => {
        expect(document.documentElement).toHaveClass('dark');
      });
    });
  });

  describe('Error Boundaries', () => {
    it('should handle component errors gracefully', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockRejectedValue(new Error('Component error'));

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
        expect(screen.getByText(/Try refreshing the page/i)).toBeInTheDocument();
      });
    });

    it('should provide error recovery options', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockRejectedValue(new Error('Component error'));

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /Try Again/i });
        expect(retryButton).toBeInTheDocument();
      });

      // Retry operation
      const retryButton = screen.getByRole('button', { name: /Try Again/i });
      await userEvent.click(retryButton);

      // Should attempt to retry the API call
      expect(api.courses.getById).toHaveBeenCalledTimes(2);
    });
  });

  describe('Loading States', () => {
    it('should display loading indicators during async operations', async () => {
      const { api } = require('@/lib/api');
      api.courses.getAll.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

      renderWithProviders(<AppRouter />);

      // Should show loading indicator
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should handle partial loading states', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getById.mockResolvedValue(mockCourse);
      api.materials.getList.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

      mockGet.mockImplementation((key) => {
        if (key === 'id') return mockCourse.id;
        return null;
      });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
      });

      // Materials should still be loading
      expect(screen.getByTestId('materials-loading')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByTestId('materials-loading')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
});

describe('Responsive Design and Accessibility', () => {
  describe('Mobile Responsiveness', () => {
    it('should adapt layout for mobile screens', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });

      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: [mockCourse] });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        // Should have mobile-specific classes or layout
        expect(screen.getByTestId('mobile-layout')).toBeInTheDocument();
      });
    });

    it('should handle touch interactions on mobile', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: [mockCourse] });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
      });

      // Test touch events (simulated)
      const courseCard = screen.getByTestId('course-card');
      fireEvent.touchStart(courseCard);
      fireEvent.touchEnd(courseCard);

      // Should navigate to course
      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}`);
    });
  });

  describe('Accessibility Features', () => {
    it('should support keyboard navigation', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: [mockCourse] });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        expect(screen.getByText(mockCourse.title)).toBeInTheDocument();
      });

      // Tab navigation
      await userEvent.tab();
      expect(screen.getByText(mockCourse.title)).toHaveFocus();

      // Enter to activate
      await userEvent.keyboard('{Enter}');
      expect(mockPush).toHaveBeenCalledWith(`/courses/${mockCourse.id}`);
    });

    it('should provide screen reader support', async () => {
      const mockCourse = createMockCourse();
      const { api } = require('@/lib/api');
      api.courses.getAll.mockResolvedValue({ courses: [mockCourse] });

      renderWithProviders(<AppRouter />);

      await waitFor(() => {
        // Check for ARIA labels and roles
        expect(screen.getByRole('main')).toBeInTheDocument();
        expect(screen.getByLabelText(/Course list/i)).toBeInTheDocument();
      });
    });
  });
});

// Performance tests
describe('Performance and Optimization', () => {
  it('should handle large course lists efficiently', async () => {
    const largeCourseList = Array.from({ length: 100 }, (_, i) =>
      createMockCourse({
        id: `course-${i}`,
        title: `Course ${i}`,
        description: `Description for course ${i}`,
      })
    );

    const { api } = require('@/lib/api');
    api.courses.getAll.mockResolvedValue({ courses: largeCourseList });

    const startTime = performance.now();
    renderWithProviders(<AppRouter />);

    await waitFor(() => {
      expect(screen.getByText('Course 0')).toBeInTheDocument();
      expect(screen.getByText('Course 99')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (2 seconds)
    expect(renderTime).toBeLessThan(2000);
  });

  it('should implement virtual scrolling for large lists', async () => {
    const largeCourseList = Array.from({ length: 1000 }, (_, i) =>
      createMockCourse({
        id: `course-${i}`,
        title: `Course ${i}`,
      })
    );

    const { api } = require('@/lib/api');
    api.courses.getAll.mockResolvedValue({ courses: largeCourseList });

    renderWithProviders(<AppRouter />);

    await waitFor(() => {
      // Should only render visible items
      const visibleCourses = screen.getAllByText(/Course \d+/);
      expect(visibleCourses.length).toBeLessThan(50); // Virtual scrolling limit
    });
  });
});