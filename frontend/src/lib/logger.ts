/**
 * Centralized Logging System for Tutor-AI Frontend
 *
 * A comprehensive logging utility with structured logging, performance monitoring,
 * error tracking, and development-friendly features.
 *
 * Features:
 * - Structured JSON logging with correlation IDs
 * - Multiple log levels (DEBUG, INFO, WARN, ERROR)
 * - Performance monitoring and timing
 * - Error boundary integration
 * - API request/response logging
 * - User interaction tracking
 * - Environment-aware logging
 * - Remote logging capabilities
 * - Console formatting for development
 */

import { config } from './config'

// Log levels
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4,
}

// Log entry interface
export interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  category: string
  correlationId?: string
  userId?: string
  sessionId?: string
  component?: string
  action?: string
  metadata?: Record<string, any>
  error?: Error | string
  stack?: string
  userAgent?: string
  url?: string
  performance?: PerformanceMetrics
}

// Performance metrics interface
export interface PerformanceMetrics {
  duration?: number
  memoryUsed?: number
  componentName?: string
  operationType?: string
  startTime?: number
  endTime?: number
}

// Logger configuration interface
export interface LoggerConfig {
  level: LogLevel
  enableConsole: boolean
  enableRemote: boolean
  enablePerformance: boolean
  remoteEndpoint?: string
  batchSize: number
  flushInterval: number
  maxRetries: number
  sanitizeData: boolean
  correlationIdHeader: string
}

// Default configuration
const DEFAULT_CONFIG: LoggerConfig = {
  level: config.debug.enabled ? LogLevel.DEBUG : LogLevel.INFO,
  enableConsole: true,
  enableRemote: config.analytics.enabled,
  enablePerformance: config.debug.showPerformanceMetrics,
  remoteEndpoint: config.analytics.apiEndpoint,
  batchSize: config.analytics.batchSize,
  flushInterval: config.analytics.flushInterval,
  maxRetries: 3,
  sanitizeData: true,
  correlationIdHeader: 'X-Correlation-ID',
}

/**
 * Main Logger class
 */
class Logger {
  private config: LoggerConfig
  private sessionId: string
  private userId?: string
  private logQueue: LogEntry[] = []
  private flushTimer?: ReturnType<typeof setInterval>
  private performanceMap: Map<string, PerformanceMetrics> = new Map()

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.sessionId = this.generateSessionId()

    // Start flush timer for remote logging
    if (this.config.enableRemote && this.config.remoteEndpoint) {
      this.startFlushTimer()
    }

    // Handle page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.flush(true) // Force flush on page unload
      })
    }
  }

  // Core logging methods
  debug(message: string, metadata?: Record<string, any>, category: string = 'app'): void {
    this.log(LogLevel.DEBUG, message, category, metadata)
  }

  info(message: string, metadata?: Record<string, any>, category: string = 'app'): void {
    this.log(LogLevel.INFO, message, category, metadata)
  }

  warn(message: string, metadata?: Record<string, any>, category: string = 'app'): void {
    this.log(LogLevel.WARN, message, category, metadata)
  }

  error(message: string, error?: Error | string, metadata?: Record<string, any>, category: string = 'app'): void {
    const errorMetadata = {
      ...metadata,
      errorMessage: error instanceof Error ? error.message : error,
      errorStack: error instanceof Error ? error.stack : undefined,
      errorName: error instanceof Error ? error.name : 'UnknownError'
    }

    this.log(LogLevel.ERROR, message, category, errorMetadata, error)
  }

  fatal(message: string, error?: Error | string, metadata?: Record<string, any>, category: string = 'app'): void {
    const errorMetadata = {
      ...metadata,
      errorMessage: error instanceof Error ? error.message : error,
      errorStack: error instanceof Error ? error.stack : undefined,
      errorName: error instanceof Error ? error.name : 'UnknownError',
      critical: true
    }

    this.log(LogLevel.FATAL, message, category, errorMetadata, error)
  }

  // Specialized logging methods
  apiRequest(method: string, url: string, headers?: Record<string, any>, body?: any): void {
    this.info(
      `API Request: ${method} ${url}`,
      {
        type: 'api_request',
        method,
        url,
        headers: this.sanitizeHeaders(headers),
        bodySize: body ? JSON.stringify(body).length : 0,
        hasBody: !!body
      },
      'api'
    )
  }

  apiResponse(method: string, url: string, status: number, duration: number, size?: number): void {
    const level = status >= 500 ? LogLevel.ERROR : status >= 400 ? LogLevel.WARN : LogLevel.INFO

    this.log(
      level,
      `API Response: ${method} ${url} - ${status} (${duration}ms)`,
      'api',
      {
        type: 'api_response',
        method,
        url,
        status,
        duration,
        responseSize: size
      }
    )
  }

  userAction(action: string, component: string, metadata?: Record<string, any>): void {
    this.info(
      `User Action: ${action} in ${component}`,
      {
        type: 'user_action',
        action,
        component,
        ...metadata
      },
      'user'
    )
  }

  performance(operation: string, duration: number, metadata?: Record<string, any>): void {
    this.info(
      `Performance: ${operation} (${duration}ms)`,
      {
        type: 'performance',
        operation,
        duration,
        ...metadata
      },
      'performance'
    )
  }

  // Performance timing utilities
  startTimer(operation: string): string {
    const timerId = `${operation}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    if (typeof performance !== 'undefined') {
      const startTime = performance.now()
      this.performanceMap.set(timerId, {
        startTime,
        operationType: operation,
        componentName: operation
      })
    }

    return timerId
  }

  endTimer(timerId: string, metadata?: Record<string, any>): number {
    const metrics = this.performanceMap.get(timerId)
    if (!metrics || !metrics.startTime) {
      return 0
    }

    const endTime = typeof performance !== 'undefined' ? performance.now() : Date.now()
    const duration = endTime - metrics.startTime

    this.performance(
      metrics.operationType || 'unknown_operation',
      duration,
      {
        ...metadata,
        timerId
      }
    )

    this.performanceMap.delete(timerId)
    return duration
  }

  // Context-aware logging
  withContext(context: { userId?: string; component?: string; correlationId?: string }): LoggerWithContext {
    return new LoggerWithContext(this, context)
  }

  // Session management
  setUserId(userId: string): void {
    this.userId = userId
  }

  getSessionId(): string {
    return this.sessionId
  }

  // Main log method
  private log(
    level: LogLevel,
    message: string,
    category: string,
    metadata?: Record<string, any>,
    error?: Error | string
  ): void {
    // Skip if below configured level
    if (level < this.config.level) {
      return
    }

    // Create log entry
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      category,
      correlationId: this.getCorrelationId(),
      userId: this.userId,
      sessionId: this.sessionId,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      metadata: this.config.sanitizeData ? this.sanitizeData(metadata) : metadata,
      error,
      stack: error instanceof Error ? error.stack : undefined
    }

    // Console logging
    if (this.config.enableConsole) {
      this.logToConsole(entry)
    }

    // Remote logging
    if (this.config.enableRemote) {
      this.logQueue.push(entry)

      // Flush immediately for errors
      if (level >= LogLevel.ERROR) {
        this.flush()
      }
    }
  }

  // Console logging with formatting
  private logToConsole(entry: LogEntry): void {
    const levelNames = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
    const levelColors = ['#6B7280', '#3B82F6', '#F59E0B', '#EF4444', '#7C2D12']
    const levelName = levelNames[entry.level]
    const color = levelColors[entry.level]

    // Format for development
    if (config.debug.enabled) {
      const style = `color: ${color}; font-weight: bold;`
      const prefix = `%c[${levelName}]%c ${entry.category}%c ${entry.message}`
      const args = [style, 'color: #6B7280;', 'color: inherit;']

      if (entry.metadata && Object.keys(entry.metadata).length > 0) {
        console.group(prefix, ...args)
        console.log('Metadata:', entry.metadata)
        if (entry.error) {
          console.error('Error:', entry.error)
        }
        console.groupEnd()
      } else {
        console.log(prefix, ...args)
        if (entry.error) {
          console.error(entry.error)
        }
      }
    } else {
      // Simple format for production
      const logMethod = entry.level >= LogLevel.ERROR ? console.error :
                       entry.level >= LogLevel.WARN ? console.warn :
                       console.log

      logMethod(`[${levelName}] ${entry.category}: ${entry.message}`, entry.metadata || '')
    }
  }

  // Remote logging
  private async flush(force: boolean = false): Promise<void> {
    if (!this.config.enableRemote || !this.config.remoteEndpoint || this.logQueue.length === 0) {
      return
    }

    // Only flush if we have enough entries or if forced
    if (!force && this.logQueue.length < this.config.batchSize) {
      return
    }

    const entries = this.logQueue.splice(0, this.config.batchSize)

    try {
      await this.sendLogs(entries)
    } catch (error) {
      // Re-queue failed logs for retry
      this.logQueue.unshift(...entries)
      console.error('Failed to send logs:', error)
    }
  }

  private async sendLogs(entries: LogEntry[], retryCount: number = 0): Promise<void> {
    if (!this.config.remoteEndpoint) {
      return
    }

    try {
      const response = await fetch(this.config.remoteEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Version': config.app.version,
          'X-Session-ID': this.sessionId,
          ...(this.userId && { 'X-User-ID': this.userId })
        },
        body: JSON.stringify({
          logs: entries,
          metadata: {
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
            url: typeof window !== 'undefined' ? window.location.href : undefined,
            timestamp: new Date().toISOString(),
            version: config.app.version
          }
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      if (retryCount < this.config.maxRetries) {
        // Exponential backoff
        const delay = Math.pow(2, retryCount) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
        return this.sendLogs(entries, retryCount + 1)
      }

      throw error
    }
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flush()
    }, this.config.flushInterval)
  }

  // Utility methods
  private generateSessionId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private getCorrelationId(): string | undefined {
    if (typeof document !== 'undefined') {
      const meta = document.querySelector('meta[name="correlation-id"]')
      if (meta) {
        return meta.getAttribute('content') || undefined
      }
    }
    return undefined
  }

  private sanitizeHeaders(headers?: Record<string, any>): Record<string, any> {
    if (!headers || !this.config.sanitizeData) {
      return headers || {}
    }

    const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key', 'x-auth-token']
    const sanitized = { ...headers }

    for (const header of sensitiveHeaders) {
      if (sanitized[header]) {
        sanitized[header] = '***REDACTED***'
      }
    }

    return sanitized
  }

  private sanitizeData(data?: Record<string, any>): Record<string, any> {
    if (!data || !this.config.sanitizeData) {
      return data || {}
    }

    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth', 'credential']
    const sanitized = { ...data }

    const sanitizeValue = (value: any): any => {
      if (Array.isArray(value)) {
        return value.map(sanitizeValue)
      }

      if (value && typeof value === 'object') {
        const result: Record<string, any> = {}
        for (const [k, v] of Object.entries(value)) {
          const keyLower = k.toLowerCase()
          if (sensitiveKeys.some(sensitive => keyLower.includes(sensitive))) {
            result[k] = '***REDACTED***'
          } else {
            result[k] = sanitizeValue(v)
          }
        }
        return result
      }

      return value
    }

    return sanitizeValue(sanitized)
  }

  // Cleanup
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
    }
    this.flush(true) // Final flush
  }
}

/**
 * Logger with context
 */
class LoggerWithContext {
  private logger: Logger
  private context: { userId?: string; component?: string; correlationId?: string }

  constructor(logger: Logger, context: { userId?: string; component?: string; correlationId?: string }) {
    this.logger = logger
    this.context = context
  }

  debug(message: string, metadata?: Record<string, any>): void {
    this.logger.debug(message, { ...this.context, ...metadata }, this.context.component || 'app')
  }

  info(message: string, metadata?: Record<string, any>): void {
    this.logger.info(message, { ...this.context, ...metadata }, this.context.component || 'app')
  }

  warn(message: string, metadata?: Record<string, any>): void {
    this.logger.warn(message, { ...this.context, ...metadata }, this.context.component || 'app')
  }

  error(message: string, error?: Error | string, metadata?: Record<string, any>): void {
    this.logger.error(message, error, { ...this.context, ...metadata }, this.context.component || 'app')
  }

  fatal(message: string, error?: Error | string, metadata?: Record<string, any>): void {
    this.logger.fatal(message, error, { ...this.context, ...metadata }, this.context.component || 'app')
  }

  userAction(action: string, metadata?: Record<string, any>): void {
    this.logger.userAction(action, this.context.component || 'unknown', metadata)
  }

  performance(operation: string, duration: number, metadata?: Record<string, any>): void {
    this.logger.performance(operation, duration, { ...this.context, ...metadata })
  }

  startTimer(operation: string): string {
    return this.logger.startTimer(operation)
  }

  endTimer(timerId: string, metadata?: Record<string, any>): number {
    return this.logger.endTimer(timerId, { ...this.context, ...metadata })
  }
}

/**
 * Performance timer utility
 */
export class PerformanceTimer {
  private logger: Logger
  private timerId?: string
  private operation: string
  private metadata?: Record<string, any>

  constructor(logger: Logger, operation: string, metadata?: Record<string, any>) {
    this.logger = logger
    this.operation = operation
    this.metadata = metadata
    this.timerId = logger.startTimer(operation)
  }

  end(additionalMetadata?: Record<string, any>): number {
    if (!this.timerId) {
      return 0
    }

    const finalMetadata = { ...this.metadata, ...additionalMetadata }
    return this.logger.endTimer(this.timerId, finalMetadata)
  }
}

/**
 * Global logger instance
 */
export const logger = new Logger()

/**
 * Utility functions
 */
export const createLogger = (config: Partial<LoggerConfig> = {}): Logger => {
  return new Logger(config)
}

export const createTimer = (operation: string, metadata?: Record<string, any>): PerformanceTimer => {
  return new PerformanceTimer(logger, operation, metadata)
}

export const withContext = (context: { userId?: string; component?: string; correlationId?: string }): LoggerWithContext => {
  return logger.withContext(context)
}

// Error boundary integration
export const logErrorBoundary = (error: Error, errorInfo: any, component: string): void => {
  logger.fatal(
    `React Error Boundary: ${error.message}`,
    error,
    {
      component,
      errorInfo,
      stack: errorInfo.componentStack,
      type: 'react_error_boundary'
    },
    'react'
  )
}

// Unhandled promise rejection handler
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    logger.fatal(
      'Unhandled Promise Rejection',
      event.reason,
      {
        type: 'unhandled_promise_rejection',
        promise: event.promise
      },
      'promise'
    )
  })

  window.addEventListener('error', (event) => {
    logger.fatal(
      'Global JavaScript Error',
      event.error,
      {
        type: 'global_error',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      },
      'javascript'
    )
  })
}

// Export default logger
export default logger
