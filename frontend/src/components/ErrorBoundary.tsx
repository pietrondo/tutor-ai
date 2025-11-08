/**
 * Error Boundary Component
 * Catches JavaScript errors in child components and displays fallback UI
 */

'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    })

    // Log error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // In production, you might want to send this to an error reporting service
    // Example: Sentry.captureException(error)
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="flex justify-center mb-6">
              <div className="p-3 bg-red-100 rounded-full">
                <AlertTriangle className="h-8 w-8 text-red-600" />
              </div>
            </div>

            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Oops! Qualcosa è andato storto
            </h1>

            <p className="text-gray-600 mb-6">
              Si è verificato un errore imprevisto. Il nostro team è stato informato e sta lavorando per risolvere il problema.
            </p>

            {/* Error details in development */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                  Dettagli errore (sviluppo)
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-800 max-h-40 overflow-auto">
                  <div className="mb-2">
                    <strong>Error:</strong> {this.state.error.message}
                  </div>
                  <div className="mb-2">
                    <strong>Stack:</strong>
                    <pre className="whitespace-pre-wrap">
                      {this.state.error.stack}
                    </pre>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre className="whitespace-pre-wrap text-xs">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={this.handleRetry}
                className="flex-1"
                variant="outline"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Riprova
              </Button>

              <Button
                onClick={this.handleReload}
                className="flex-1"
              >
                Ricarica pagina
              </Button>
            </div>

            <div className="mt-6 text-xs text-gray-500">
              Se il problema persiste, contatta il supporto tecnico.
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Hook for handling async errors in function components
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const catchError = React.useCallback((error: Error) => {
    console.error('Async error caught:', error)
    setError(error)
  }, [])

  // Throw error to be caught by ErrorBoundary
  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return { catchError, resetError }
}

// Component to wrap async operations that might fail
interface AsyncBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error) => void
}

export function AsyncBoundary({ children, fallback, onError }: AsyncBoundaryProps) {
  const { catchError, resetError } = useErrorHandler()

  const handleAsyncError = React.useCallback((error: Error) => {
    catchError(error)
    if (onError) {
      onError(error)
    }
  }, [catchError, onError])

  return (
    <ErrorBoundary
      fallback={fallback}
      onError={(error, errorInfo) => {
        handleAsyncError(error)
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

// HOC to add error boundary to components
export function withErrorBoundary<T extends object>(
  Component: React.ComponentType<T>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
  return function WrappedComponent(props: T) {
    return (
      <ErrorBoundary fallback={fallback} onError={onError}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}