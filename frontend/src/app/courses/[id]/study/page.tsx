/**
 * Pagina Studio Integrato
 * Combina PDF reader, chat tutor e note in un'unica interfaccia
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams, useRouter, usePathname } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  BookOpen,
  MessageCircle,
  FileText,
  Settings,
  Maximize2,
  RefreshCw
} from 'lucide-react';
import { Course } from '@/types';

// Dynamic import to avoid server-side rendering issues with PDF.js
// Lettore avanzato con annotazioni e note
const EnhancedPDFReader = dynamic(() => import('@/components/EnhancedPDFReader'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-4 text-gray-600">Caricamento lettore PDF...</p>
      </div>
    </div>
  )
});

const IntegratedChatTutor = dynamic(() => import('@/components/IntegratedChatTutor'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Caricamento chat...</p>
      </div>
    </div>
  )
});

// Extended Book interface for StudyPage needs
interface StudyMaterial {
  filename: string;
  relative_path: string;
  size?: number;
  uploaded_at?: string;
  file_path?: string;
  pdf_url?: string;
}

interface StudyBook {
  id: string;
  title: string;
  pdf_url?: string;
  total_pages: number;
  description?: string;
  file_size?: number;
  uploaded_at?: string;
  materials_count?: number;
  materials?: StudyMaterial[];
}

// Extended Course interface for StudyPage needs
interface StudyCourse extends Course {
  books?: StudyBook[];
  materials?: any[];
}

export default function StudyPage() {
  const params = useParams();
  const courseId = params.id as string;
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Stati
  const [course, setCourse] = useState<StudyCourse | null>(null);
  const [selectedBook, setSelectedBook] = useState<StudyBook | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Layout states
  const [layoutMode, setLayoutMode] = useState<'split' | 'pdf-focus' | 'chat-focus'>('split');
  const [showBookSelector, setShowBookSelector] = useState(false);
  const [user, setUser] = useState<{ id: string; name: string } | null>(null);
  const [activeMaterial, setActiveMaterial] = useState<StudyMaterial | null>(null);

  const updateBookQueryParams = useCallback(
    (bookId: string | null, pdfFilename?: string | null) => {
      if (!searchParams) return;

      const params = new URLSearchParams(searchParams.toString());

      if (bookId) {
        params.set('book', bookId);
      } else {
        params.delete('book');
      }

      if (pdfFilename) {
        params.set('pdf', pdfFilename);
      } else {
        params.delete('pdf');
      }

      const queryString = params.toString();
      router.replace(`${pathname}${queryString ? `?${queryString}` : ''}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  const getDefaultMaterialForBook = useCallback((book: StudyBook | null): StudyMaterial | null => {
    if (!book) return null;
    const materials = book.materials || [];
    if (materials.length > 0) {
      return materials[0];
    }

    if (book.pdf_url) {
      const derivedName = decodeURIComponent(book.pdf_url.split('/').pop() || `${book.id}.pdf`);
      return {
        filename: derivedName,
        relative_path: derivedName,
        pdf_url: book.pdf_url,
        file_path: book.pdf_url,
        size: undefined,
        uploaded_at: undefined
      };
    }

    return null;
  }, []);

  const pickMaterialForBook = useCallback((book: StudyBook, requestedFilename: string | null): StudyMaterial | null => {
    const materials = book.materials || [];
    if (requestedFilename) {
      const match = materials.find(material =>
        material.filename === requestedFilename ||
        material.relative_path === requestedFilename ||
        material.relative_path?.endsWith(`/${requestedFilename}`)
      );
      if (match) {
        return match;
      }
    }

    if (materials.length > 0) {
      return materials[0];
    }

    return getDefaultMaterialForBook(book);
  }, [getDefaultMaterialForBook]);

  // Carica dati iniziali
  useEffect(() => {
    loadCourseData();
    loadUserData();
  }, [courseId]);

  const loadCourseData = async (retryCount = 0) => {
    try {
      setIsLoading(true);
      setError(null);

      // Validate courseId
      if (!courseId) {
        throw new Error('ID corso non valido');
      }

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}`);

      if (response.status === 404) {
        throw new Error('Corso non trovato');
      } else if (!response.ok) {
        throw new Error(`Errore server: ${response.status} ${response.statusText}`);
      }

      const apiResponse = await response.json();

      // Validate response structure
      if (!apiResponse || !apiResponse.course) {
        throw new Error('Formato risposta non valido');
      }

      const courseData = apiResponse.course;

      // Backend now provides both materials and books arrays
      if (courseData) {
        // Ensure books array exists even if empty
        const transformedCourse: StudyCourse = {
          ...courseData,
          books: courseData.books || []
        };
        setCourse(transformedCourse);

        // Select first book available
        if (!transformedCourse.books || transformedCourse.books.length === 0) {
          console.warn('Nessun libro trovato per il corso:', courseData.name || courseData.id);
        }
      } else {
        throw new Error('Dati corso non disponibili');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto';
      console.error('Errore caricamento corso:', err);

      // Retry logic for network errors
      if (retryCount < 2 && (errorMessage.includes('fetch') || errorMessage.includes('network'))) {
        console.log(`Retry attempt ${retryCount + 1}...`);
        setTimeout(() => loadCourseData(retryCount + 1), 1000 * (retryCount + 1));
        return;
      }

      setError(errorMessage);
      // Reset state on error
      setCourse(null);
      setSelectedBook(null);
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserData = async () => {
    try {
      // In una implementazione reale, questo verrebbe da un auth context
      const userData = {
        id: 'demo-user',
        name: 'Utente Demo'
      };
      setUser(userData);
    } catch (err) {
      console.error('Errore caricamento utente:', err);
    }
  };

  const handleBookSelect = (book: StudyBook) => {
    setSelectedBook(book);
    setShowBookSelector(false);
    const defaultMaterial = getDefaultMaterialForBook(book);
    setActiveMaterial(defaultMaterial);
    updateBookQueryParams(book.id, defaultMaterial?.filename || null);
  };

  const handleAnnotationCreate = (annotation: any) => {
    console.log('Annotazione creata:', annotation);
    // Potrebbe aggiornare contesto chat o mostrare notifica
  };

  const handleNoteCreate = (note: any) => {
    console.log('Nota creata:', note);
    // Potrebbe mostrare notifica o aggiornare conteggi
  };

  const handleProfileUpdate = (profile: any) => {
    console.log('Profilo aggiornato:', profile);
    // Potrebbe mostrare badge o aggiornare UI
  };

  const handleChatWithContext = (context: any) => {
    console.log('Context per chat:', context);
    // Gestisce quando il PDF reader passa contesto alla chat
  };

  const handleRefreshCourse = () => {
    loadCourseData();
  };

  useEffect(() => {
    if (!course || !course.books || course.books.length === 0) {
      setSelectedBook(null);
      setActiveMaterial(null);
      return;
    }

    const queryBookId = searchParams?.get('book');
    let nextBook: StudyBook | null = null;

    if (queryBookId) {
      nextBook = course.books.find(book => book.id === queryBookId) || null;
    }

    if (!nextBook) {
      nextBook = course.books[0];
    }

    setSelectedBook(prev => {
      if (prev && nextBook && prev.id === nextBook.id) {
        return prev;
      }
      return nextBook;
    });
  }, [course, searchParams]);

  useEffect(() => {
    if (!selectedBook) {
      setActiveMaterial(null);
      return;
    }

    const queryPdf = searchParams?.get('pdf') || null;
    const nextMaterial = pickMaterialForBook(selectedBook, queryPdf);
    setActiveMaterial(nextMaterial);

    if (nextMaterial) {
      const matchesQuery = queryPdf && (queryPdf === nextMaterial.filename || queryPdf === nextMaterial.relative_path);
      if (!matchesQuery && nextMaterial.filename) {
        updateBookQueryParams(selectedBook.id, nextMaterial.filename);
      }
    } else if (!queryPdf) {
      updateBookQueryParams(selectedBook.id, null);
    }
  }, [selectedBook, searchParams, updateBookQueryParams, pickMaterialForBook]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento corso...</p>
          <p className="text-sm text-gray-500 mt-2">Stiamo preparando i tuoi materiali di studio</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-600 text-xl mb-4">⚠️ Errore</div>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (!course || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Dati non disponibili</p>
        </div>
      </div>
    );
  }

  const resolvedPdfUrl = selectedBook ? (activeMaterial?.pdf_url || selectedBook.pdf_url || '') : '';
  const resolvedPdfFilename = selectedBook
    ? (activeMaterial?.filename || decodeURIComponent((selectedBook.pdf_url || `${selectedBook.id}.pdf`).split('/').pop() || `${selectedBook.id}.pdf`))
    : '';
  const resolvedPdfPath = selectedBook
    ? (activeMaterial?.file_path || activeMaterial?.pdf_url || selectedBook.pdf_url || '')
    : '';

  // Layout classes based on mode
  const getLayoutClasses = () => {
    switch (layoutMode) {
      case 'pdf-focus':
        return 'grid-cols-12 gap-0';
      case 'chat-focus':
        return 'grid-cols-12 gap-0';
      case 'split':
      default:
        return 'grid-cols-12 gap-4';
    }
  };

  const getPDFColumnClasses = () => {
    switch (layoutMode) {
      case 'pdf-focus':
        return 'col-span-12';
      case 'chat-focus':
        return 'col-span-0 hidden';
      case 'split':
      default:
        return 'col-span-7';
    }
  };

  const getChatColumnClasses = () => {
    switch (layoutMode) {
      case 'pdf-focus':
        return 'col-span-0 hidden';
      case 'chat-focus':
        return 'col-span-12';
      case 'split':
      default:
        return 'col-span-5';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900">{course.name}</h1>
            <button
              onClick={handleRefreshCourse}
              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
              title="Aggiorna corso"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {/* Book selector */}
            {course.books && course.books.length > 1 && (
              <div className="relative">
                <button
                  onClick={() => setShowBookSelector(!showBookSelector)}
                  className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                >
                  <BookOpen className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    {selectedBook ? selectedBook.title : 'Seleziona libro'}
                  </span>
                </button>

                {showBookSelector && (
                  <div className="absolute top-10 left-0 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-[300px]">
                    <div className="p-2">
                      {course.books && course.books.map(book => (
                        <button
                          key={book.id}
                          onClick={() => handleBookSelect(book)}
                          className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 flex items-center space-x-2 ${
                            selectedBook?.id === book.id ? 'bg-blue-50 text-blue-700' : 'text-gray-900'
                          }`}
                        >
                          <BookOpen className="w-4 h-4" />
                          <span className="text-sm font-medium">{book.title}</span>
                          <span className="text-xs text-gray-500 ml-auto">
                            {book.total_pages} pagine
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {/* Layout controls */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setLayoutMode('split')}
                className={`p-2 rounded ${
                  layoutMode === 'split' ? 'bg-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Vista divisa"
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={() => setLayoutMode('pdf-focus')}
                className={`p-2 rounded ${
                  layoutMode === 'pdf-focus' ? 'bg-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Focus PDF"
              >
                <FileText className="w-4 h-4" />
              </button>
              <button
                onClick={() => setLayoutMode('chat-focus')}
                className={`p-2 rounded ${
                  layoutMode === 'chat-focus' ? 'bg-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Focus Chat"
              >
                <MessageCircle className="w-4 h-4" />
              </button>
            </div>

            {/* User info */}
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>Benvenuto, {user.name}</span>
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-medium">
                  {user.name.charAt(0).toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 p-4 overflow-hidden">
        {selectedBook ? (
          <div className={`grid ${getLayoutClasses()} h-full`}>
            {/* PDF Reader */}
            <div className={`${getPDFColumnClasses()} flex flex-col`}>
              <div className="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
                <EnhancedPDFReader
                  pdfUrl={resolvedPdfUrl}
                  pdfFilename={resolvedPdfFilename}
                  pdfPath={resolvedPdfPath}
                  bookId={selectedBook.id}
                  courseId={courseId}
                  userId={user.id}
                  onAnnotationCreate={handleAnnotationCreate}
                  onChatWithContext={handleChatWithContext}
                />
              </div>
            </div>

            {/* Chat Tutor */}
            <div className={`${getChatColumnClasses()} flex flex-col`}>
              <div className="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
                <IntegratedChatTutor
                  courseId={courseId}
                  userId={user.id}
                  bookId={selectedBook.id}
                  currentContext={{
                    bookTitle: selectedBook.title,
                    totalPages: selectedBook.total_pages
                  }}
                  onNoteCreate={handleNoteCreate}
                  onProfileUpdate={handleProfileUpdate}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <BookOpen className="mx-auto h-16 w-16 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                Nessun libro disponibile
              </h3>
              <p className="mt-2 text-gray-600">
                Carica prima un PDF per iniziare a studiare
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Floating action buttons for layout switching in focus modes */}
      {layoutMode !== 'split' && (
        <div className="fixed bottom-6 right-6 z-50">
          <button
            onClick={() => setLayoutMode('split')}
            className="bg-blue-500 text-white p-3 rounded-full shadow-lg hover:bg-blue-600 transition-colors"
            title="Torna a vista divisa"
          >
            <Maximize2 className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
