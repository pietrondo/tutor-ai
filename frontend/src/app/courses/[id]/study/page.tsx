/**
 * Pagina Studio Integrato
 * Combina PDF reader, chat tutor e note in un'unica interfaccia
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import EnhancedPDFReader from '@/components/EnhancedPDFReader';
import IntegratedChatTutor from '@/components/IntegratedChatTutor';
import {
  BookOpen,
  MessageCircle,
  FileText,
  Brain,
  Settings,
  X,
  Maximize2,
  Minimize2
} from 'lucide-react';

interface Book {
  id: string;
  title: string;
  pdf_url: string;
  total_pages: number;
}

interface Course {
  id: string;
  title: string;
  description: string;
  books: Book[];
}

export default function StudyPage() {
  const params = useParams();
  const courseId = params.id as string;

  // Stati
  const [course, setCourse] = useState<Course | null>(null);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Layout states
  const [layoutMode, setLayoutMode] = useState<'split' | 'pdf-focus' | 'chat-focus'>('split');
  const [showBookSelector, setShowBookSelector] = useState(false);
  const [user, setUser] = useState<{ id: string; name: string } | null>(null);

  // Carica dati iniziali
  useEffect(() => {
    loadCourseData();
    loadUserData();
  }, [courseId]);

  const loadCourseData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/courses/${courseId}`);
      if (!response.ok) throw new Error('Errore caricamento corso');

      const data = await response.json();
      setCourse(data);

      // Seleziona primo libro disponibile
      if (data.books && data.books.length > 0) {
        setSelectedBook(data.books[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto');
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

  const handleBookSelect = (book: Book) => {
    setSelectedBook(book);
    setShowBookSelector(false);
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento corso...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Errore</div>
          <p className="text-gray-600">{error}</p>
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
            <h1 className="text-xl font-semibold text-gray-900">{course.title}</h1>

            {/* Book selector */}
            {course.books.length > 1 && (
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
                      {course.books.map(book => (
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
                  pdfUrl={selectedBook.pdf_url}
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