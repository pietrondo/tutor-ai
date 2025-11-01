import { Suspense } from 'react'
import { ChatWrapper } from '@/components/ChatWrapper'

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Chat con il Tutor AI</h1>
          <p className="text-gray-600">
            Fai domande sui tuoi materiali di studio e ricevi risposte personalizzate
          </p>
        </div>
        <div className="card p-8 text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Caricamento chat...</p>
        </div>
      </div>
    }>
      <ChatWrapper />
    </Suspense>
  )
}