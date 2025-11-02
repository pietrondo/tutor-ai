import { Suspense } from 'react'
import { SessionChatWrapper } from '@/components/SessionChatWrapper'

interface PageProps {
  params: {
    sessionId: string
  }
  searchParams: {
    planId?: string
    courseId?: string
    sessionTitle?: string
  }
}

export default function SessionChatPage({ params, searchParams }: PageProps) {
  return (
    <Suspense fallback={
      <div className="max-w-4xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Sessione di Studio</h1>
          <p className="text-gray-600">
            Chat dedicata per questa sessione di studio
          </p>
        </div>
        <div className="card p-8 text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Caricamento sessione...</p>
        </div>
      </div>
    }>
      <SessionChatWrapper
        sessionId={params.sessionId}
        planId={searchParams.planId || ''}
        courseId={searchParams.courseId || ''}
        sessionTitle={searchParams.sessionTitle || 'Sessione di Studio'}
      />
    </Suspense>
  )
}