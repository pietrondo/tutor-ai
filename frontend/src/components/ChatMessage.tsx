'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { User, Bot, FileText, Target, Clock, X, CheckCircle } from 'lucide-react'

interface Source {
  source: string
  chunk_index: number
  relevance_score: number
}

interface QuizSuggestion {
  auto_detected: boolean
  confidence: number
  difficulty: string
  num_questions: number
  topic: string
  quiz_type: string
  suggested_quizzes?: Array<{
    concept_id: string
    concept_name: string
    quiz_type: string
    difficulty: string
    estimated_time: number
    description: string
  }>
  fallback_mode?: boolean
  message?: string
  error?: string
}

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  sources?: Source[]
  quiz_suggestion?: QuizSuggestion
}

interface ChatMessageProps {
  message: Message
  onQuizStart?: (quizSuggestion: QuizSuggestion) => void
}

export function ChatMessage({ message, onQuizStart }: ChatMessageProps) {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('it-IT', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 slide-in-up`}>
      <div className={`max-w-4xl ${isUser ? 'order-2' : 'order-1'} w-full`}>
        <div className="flex items-center mb-3 space-x-3">
          <div className={`flex items-center space-x-2 ${isUser ? 'justify-end' : ''}`}>
            {isUser ? (
              <>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-700">Tu</span>
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                </div>
                <span className="text-xs text-gray-400">{formatTime(message.timestamp)}</span>
              </>
            ) : (
              <>
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">Tutor AI</span>
                </div>
                <span className="text-xs text-gray-400">{formatTime(message.timestamp)}</span>
              </>
            )}
          </div>
        </div>

        <div
          className={`chat-message ${isUser ? 'user-message' : 'assistant-message'} ${isUser ? 'ml-auto' : 'mr-auto'}`}
        >
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-6 pt-4 border-t border-gray-200/50">
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText className="h-3 w-3 text-blue-600" />
                </div>
                <span className="text-sm font-semibold text-gray-700">Fonti:</span>
                <span className="badge badge-primary text-xs">
                  {message.sources.length}
                </span>
              </div>
              <div className="space-y-2">
                {message.sources.slice(0, 3).map((source, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200 hover-lift"
                  >
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <FileText className="h-4 w-4 text-gray-500 flex-shrink-0" />
                      <span className="text-sm text-gray-700 truncate font-medium">
                        {source.source}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 ml-3">
                      <div className="w-12 bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 bg-gradient-to-r from-blue-500 to-green-500 rounded-full"
                          style={{ width: `${source.relevance_score * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-gray-600 min-w-[40px] text-right">
                        {Math.round(source.relevance_score * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
                {message.sources.length > 3 && (
                  <div className="text-center py-2">
                    <span className="text-xs text-gray-500 italic bg-gray-100 px-3 py-1 rounded-full">
                      +{message.sources.length - 3} altre fonti
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Quiz Suggestion */}
          {message.quiz_suggestion && !isUser && (
            <div className="mt-6 pt-4 border-t border-gray-200/50">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Target className="h-3 w-3 text-blue-600" />
                    </div>
                    <span className="text-sm font-semibold text-blue-900">
                      {message.quiz_suggestion.auto_detected ? 'Quiz Suggerito' : 'Quiz Disponibile'}
                    </span>
                    {message.quiz_suggestion.confidence >= 0.8 && (
                      <span className="badge bg-green-100 text-green-800 text-xs">
                        Alta corrispondenza
                      </span>
                    )}
                  </div>
                  {message.quiz_suggestion.confidence >= 0.8 && (
                    <div className="flex items-center space-x-1 text-xs text-green-600">
                      <CheckCircle className="h-3 w-3" />
                      <span>{Math.round(message.quiz_suggestion.confidence * 100)}%</span>
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  {message.quiz_suggestion.message && (
                    <p className="text-sm text-blue-800">{message.quiz_suggestion.message}</p>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-blue-700">
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Argomento:</span>
                      <span className="bg-blue-100 px-2 py-1 rounded text-xs">{message.quiz_suggestion.topic}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Domande:</span>
                      <span>{message.quiz_suggestion.num_questions}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">Difficoltà:</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        message.quiz_suggestion.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                        message.quiz_suggestion.difficulty === 'hard' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {message.quiz_suggestion.difficulty === 'easy' ? 'Facile' :
                         message.quiz_suggestion.difficulty === 'hard' ? 'Difficile' : 'Medio'}
                      </span>
                    </div>
                  </div>

                  {message.quiz_suggestion.suggested_quizzes && message.quiz_suggestion.suggested_quizzes.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-blue-900">Quiz disponibili:</div>
                      {message.quiz_suggestion.suggested_quizzes.slice(0, 3).map((quiz, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-white rounded-lg border border-blue-200">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">{quiz.concept_name}</div>
                              <div className="text-xs text-gray-500">{quiz.description}</div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            <span>{quiz.estimated_time}min</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex space-x-3 pt-2">
                    <button
                      onClick={() => onQuizStart?.(message.quiz_suggestion!)}
                      className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                    >
                      <Target className="h-4 w-4" />
                      <span>Inizia Quiz</span>
                    </button>
                    <button
                      className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors"
                      onClick={() => {/* Could add dismiss functionality */}}
                    >
                      Forse dopo
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
