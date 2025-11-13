import React from 'react'
import { cn } from '@/lib/utils'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className={cn('grid grid-cols-12 gap-4 lg:gap-6')}>{children}</div>
  )
}

export default AppShell
