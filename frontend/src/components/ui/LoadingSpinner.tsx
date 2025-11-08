/**
 * Loading Spinner Component
 * Provides consistent loading states across the application
 */

'use client'

import React from 'react'
import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  text?: string
  inline?: boolean
}

export function LoadingSpinner({
  size = 'md',
  className = '',
  text,
  inline = false
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  }

  const containerClasses = inline
    ? 'flex items-center space-x-2'
    : 'flex flex-col items-center justify-center space-y-2'

  return (
    <div className={cn(containerClasses, className)}>
      <div className="relative">
        <div
          className={cn(
            'animate-spin rounded-full border-2 border-gray-200 border-t-blue-600',
            sizeClasses[size]
          )}
        />
        {size === 'lg' && (
          <div
            className={cn(
              'absolute inset-0 rounded-full border-2 border-transparent border-r-blue-400 animate-spin',
              'animation-delay-150'
            )}
          />
        )}
      </div>
      {text && (
        <p className={cn(
          'text-sm text-gray-600',
          inline ? 'ml-2' : 'mt-2'
        )}>
          {text}
        </p>
      )}
    </div>
  )
}

// Full page loading component
export function FullPageLoading({
  text = 'Caricamento...',
  className = ''
}: {
  text?: string
  className?: string
}) {
  return (
    <div className={cn(
      'fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50',
      className
    )}>
      <div className="bg-white rounded-lg p-8 shadow-lg">
        <LoadingSpinner size="lg" text={text} />
      </div>
    </div>
  )
}

// Skeleton loading component
export function SkeletonLoader({
  lines = 3,
  className = ''
}: {
  lines?: number
  className?: string
}) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-4 bg-gray-200 rounded animate-pulse',
            i === lines - 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  )
}

// Card skeleton loader
export function CardSkeleton({
  className = ''
}: {
  className?: string
}) {
  return (
    <div className={cn(
      'bg-white rounded-lg border border-gray-200 p-6 space-y-4',
      className
    )}>
      <div className="flex items-center space-x-4">
        <div className="h-12 w-12 bg-gray-200 rounded-lg animate-pulse" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
        </div>
      </div>
      <SkeletonLoader lines={2} />
      <div className="flex justify-between items-center">
        <div className="h-3 bg-gray-200 rounded w-1/4 animate-pulse" />
        <div className="h-8 bg-gray-200 rounded w-20 animate-pulse" />
      </div>
    </div>
  )
}

// Table skeleton loader
export function TableSkeleton({
  rows = 5,
  columns = 4,
  className = ''
}: {
  rows?: number
  columns?: number
  className?: string
}) {
  return (
    <div className={cn('space-y-2', className)}>
      {/* Header */}
      <div className="flex space-x-4 p-4 border-b">
        {Array.from({ length: columns }).map((_, i) => (
          <div
            key={i}
            className="h-4 bg-gray-200 rounded flex-1 animate-pulse"
          />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4 p-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <div
              key={colIndex}
              className="h-3 bg-gray-100 rounded flex-1 animate-pulse"
            />
          ))}
        </div>
      ))}
    </div>
  )
}