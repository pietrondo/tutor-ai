'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { User, Bot, FileText, Clock } from 'lucide-react'

interface Source {
  source: string
  chunk_index: number
  relevance_score: number
}

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  sources?: Source[]
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
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
        </div>
      </div>
    </div>
  )
}