/**
 * Integrated Chat Tutor
 * Componente chat avanzato con integrazione completa di note, annotazioni e adaptive learning
 */

'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
import {
  SendIcon,
  BookOpenIcon,
  FileTextIcon,
  BrainIcon,
  TrendingUpIcon,
  ClockIcon,
  UserIcon,
  BotIcon,
  LightbulbIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  Loader2Icon
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources: Array<{
    type: 'course_material' | 'user_annotation' | 'user_note';
    title: string;
    content?: string;
    page?: number;
    relevance?: number;
  }>;
  confidence: number;
  topics: string[];
  suggestedActions: string[];
  responseTime: number;
}

interface UserNote {
  id: string;
  title: string;
  content: string;
  type: string;
  createdAt: Date;
  tags: string[];
}

interface IntegratedChatTutorProps {
  courseId: string;
  userId: string;
  bookId?: string;
  currentContext?: any;
  onNoteCreate?: (note: any) => void;
  onProfileUpdate?: (profile: any) => void;
}

const IntegratedChatTutor: React.FC<IntegratedChatTutorProps> = ({
  courseId,
  userId,
  bookId,
  currentContext,
  onNoteCreate,
  onProfileUpdate
}) => {
  // Stati chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Stati contesto
  const [userNotes, setUserNotes] = useState<UserNote[]>([]);
  const [recentAnnotations, setRecentAnnotations] = useState<any[]>([]);
  const [learningProfile, setLearningProfile] = useState<any>(null);
  const [showContext, setShowContext] = useState(true);

  // States UI
  const [showNotes, setShowNotes] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showSources, setShowSources] = useState(true);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Carica dati iniziali
  useEffect(() => {
    initializeChat();
    loadUserNotes();
    loadRecentAnnotations();
    loadLearningProfile();
  }, [courseId, userId, bookId]);

  const initializeChat = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/initialize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: courseId,
          user_id: userId,
          book_id: bookId
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);

        if (data.welcome_message) {
          setMessages([{
            id: Date.now().toString(),
            role: 'assistant',
            content: data.welcome_message,
            timestamp: new Date(),
            sources: [],
            confidence: 1.0,
            topics: ['benvenuto'],
            suggestedActions: ['Inizia a fare domande', 'Esplora i materiali del corso'],
            responseTime: 0
          }]);
        }
      }
    } catch (error) {
      console.error('Errore inizializzazione chat:', error);
    }
  };

  const loadUserNotes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notes/recent?user_id=${userId}&course_id=${courseId}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setUserNotes(data.notes || []);
      }
    } catch (error) {
      console.error('Errore caricamento note:', error);
    }
  };

  const loadRecentAnnotations = async () => {
    try {
      if (!bookId) return;

      const response = await fetch(`${API_BASE_URL}/api/books/${bookId}/annotations/recent?user_id=${userId}&limit=3`);
      if (response.ok) {
        const data = await response.json();
        setRecentAnnotations(data.annotations || []);
      }
    } catch (error) {
      console.error('Errore caricamento annotazioni:', error);
    }
  };

  const loadLearningProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/learning/profile?user_id=${userId}&course_id=${courseId}`);
      if (response.ok) {
        const data = await response.json();
        setLearningProfile(data.profile);
      }
    } catch (error) {
      console.error('Errore caricamento profilo:', error);
    }
  };

  // Invia messaggio
  const sendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
      sources: [],
      confidence: 1.0,
      topics: [],
      suggestedActions: [],
      responseTime: 0
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const startTime = Date.now();

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          course_id: courseId,
          session_id: sessionId,
          message: inputMessage.trim(),
          book_id: bookId,
          include_user_notes: true,
          include_course_context: true,
          include_annotations: true
        })
      });

      const endTime = Date.now();
      const responseTime = endTime - startTime;

      if (response.ok) {
        const data = await response.json();

        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          sources: data.sources || [],
          confidence: data.confidence || 0.8,
          topics: data.topics || [],
          suggestedActions: data.suggested_actions || [],
          responseTime
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Aggiorna dati contestuali se necessario
        if (data.updated_notes) {
          await loadUserNotes();
        }

        if (data.profile_updated && onProfileUpdate) {
          await loadLearningProfile();
          onProfileUpdate(learningProfile);
        }
      } else {
        throw new Error('Errore nella risposta');
      }
    } catch (error) {
      console.error('Errore invio messaggio:', error);

      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Mi dispiace, si è verificato un errore. Per favore riprova.',
        timestamp: new Date(),
        sources: [],
        confidence: 0.0,
        topics: ['errore'],
        suggestedActions: [],
        responseTime: 0
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [inputMessage, isLoading, userId, courseId, sessionId, bookId]);

  // Auto-scroll all'ultimo messaggio
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Gestione input
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Crea nota da messaggio
  const createNoteFromMessage = async (message: ChatMessage) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notes/from-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          course_id: courseId,
          message_content: message.content,
          topics: message.topics,
          session_id: sessionId
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (onNoteCreate) {
          onNoteCreate(data.note);
        }
        await loadUserNotes();
      }
    } catch (error) {
      console.error('Errore creazione nota:', error);
    }
  };

  // Render messaggio
  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user';

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 ${isUser ? 'ml-2' : 'mr-2'}`}>
            {isUser ? (
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-white" />
              </div>
            ) : (
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <BotIcon className="w-5 h-5 text-white" />
              </div>
            )}
          </div>

          {/* Contenuto messaggio */}
          <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
            <div
              className={`px-4 py-2 rounded-lg ${
                isUser
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              } max-w-full`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>

              {/* Metadati per messaggi assistant */}
              {!isUser && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  {/* Confidence score */}
                  {message.confidence > 0 && (
                    <div className="flex items-center space-x-1 mb-1">
                      {message.confidence >= 0.8 ? (
                        <CheckCircleIcon className="w-3 h-3 text-green-500" />
                      ) : message.confidence >= 0.6 ? (
                        <AlertCircleIcon className="w-3 h-3 text-yellow-500" />
                      ) : (
                        <AlertCircleIcon className="w-3 h-3 text-red-500" />
                      )}
                      <span className="text-xs text-gray-500">
                        Confidenza: {Math.round(message.confidence * 100)}%
                      </span>
                    </div>
                  )}

                  {/* Response time */}
                  {message.responseTime > 0 && (
                    <div className="flex items-center space-x-1 mb-1">
                      <ClockIcon className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {message.responseTime}ms
                      </span>
                    </div>
                  )}

                  {/* Topics */}
                  {message.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {message.topics.map((topic, index) => (
                        <span
                          key={index}
                          className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Timestamp */}
            <div className="flex items-center space-x-2 mt-1">
              <span className="text-xs text-gray-500">
                {message.timestamp.toLocaleTimeString()}
              </span>

              {!isUser && (
                <button
                  onClick={() => createNoteFromMessage(message)}
                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                >
                  <FileTextIcon className="w-3 h-3" />
                  <span>Salva come nota</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BrainIcon className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Tutor AI</h2>
            {learningProfile && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                Adattivo
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowContext(!showContext)}
              className={`p-2 rounded ${showContext ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              title="Mostra contesto"
            >
              <BookOpenIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowNotes(!showNotes)}
              className={`p-2 rounded ${showNotes ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              title="Note recenti"
            >
              <FileTextIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowProfile(!showProfile)}
              className={`p-2 rounded ${showProfile ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              title="Profilo apprendimento"
            >
              <TrendingUpIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Pannello contesto */}
        {showContext && (
          <div className="w-80 bg-white border-r border-gray-200 p-4 overflow-y-auto">
            <div className="space-y-4">
              {/* Note recenti */}
              {userNotes.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Note Recent</h3>
                  <div className="space-y-2">
                    {userNotes.slice(0, 3).map(note => (
                      <div key={note.id} className="p-2 bg-gray-50 rounded-lg text-xs">
                        <div className="font-medium text-gray-900">{note.title}</div>
                        <div className="text-gray-600 mt-1">{note.content.substring(0, 100)}...</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Annotazioni recenti */}
              {recentAnnotations.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Annotazioni PDF</h3>
                  <div className="space-y-2">
                    {recentAnnotations.map(ann => (
                      <div key={ann.id} className="p-2 bg-yellow-50 rounded-lg text-xs">
                        <div className="font-medium text-gray-900">Pagina {ann.page_number}</div>
                        <div className="text-gray-600 mt-1">{ann.note_text || ann.text_content}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Profilo apprendimento */}
              {learningProfile && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Profilo Apprendimento</h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Stile:</span>
                      <span className="font-medium">{learningProfile.learning_style}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Difficoltà:</span>
                      <span className="font-medium">{learningProfile.preferred_difficulty}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Ritmo:</span>
                      <span className="font-medium">{learningProfile.learning_pace}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Area chat principale */}
        <div className="flex-1 flex flex-col">
          {/* Messaggi */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <BrainIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">
                    Inizia la conversazione
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Chiedimi qualsiasi cosa sui materiali del corso
                  </p>
                </div>
              </div>
            ) : (
              <>
                {messages.map(renderMessage)}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex items-center space-x-2 bg-white border border-gray-200 rounded-lg px-4 py-2">
                      <Loader2Icon className="w-4 h-4 animate-spin text-blue-600" />
                      <span className="text-sm text-gray-600">Sto pensando...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input area */}
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Fai una domanda sui materiali del corso..."
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={2}
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <SendIcon className="w-4 h-4" />
                <span>Invia</span>
              </button>
            </div>

            {/* Suggerimenti rapidi */}
            {messages.length > 0 && messages[messages.length - 1].suggestedActions.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {messages[messages.length - 1].suggestedActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(action)}
                    className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full hover:bg-gray-200 flex items-center space-x-1"
                  >
                    <LightbulbIcon className="w-3 h-3" />
                    <span>{action}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Pannello fonti */}
        {showSources && messages.length > 0 && messages[messages.length - 1].sources.length > 0 && (
          <div className="w-64 bg-white border-l border-gray-200 p-4 overflow-y-auto">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Fonti</h3>
            <div className="space-y-2">
              {messages[messages.length - 1].sources.map((source, index) => (
                <div key={index} className="p-2 bg-gray-50 rounded-lg text-xs">
                  <div className="flex items-center space-x-1 mb-1">
                    {source.type === 'course_material' && <BookOpenIcon className="w-3 h-3 text-blue-600" />}
                    {source.type === 'user_annotation' && <FileTextIcon className="w-3 h-3 text-yellow-600" />}
                    {source.type === 'user_note' && <FileTextIcon className="w-3 h-3 text-green-600" />}
                    <span className="font-medium text-gray-900">{source.title}</span>
                  </div>
                  {source.page && (
                    <div className="text-gray-600">Pagina {source.page}</div>
                  )}
                  {source.content && (
                    <div className="text-gray-600 mt-1">{source.content.substring(0, 100)}...</div>
                  )}
                  {source.relevance && (
                    <div className="flex items-center space-x-1 mt-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-1">
                        <div
                          className="bg-blue-500 h-1 rounded-full"
                          style={{ width: `${source.relevance * 100}%` }}
                        />
                      </div>
                      <span className="text-gray-500">{Math.round(source.relevance * 100)}%</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegratedChatTutor;