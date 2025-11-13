import React from 'react'
import { cn } from '@/lib/utils'

type Variant =
  | 'display'
  | 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'h5'
  | 'h6'
  | 'body'
  | 'caption'
  | 'code'

interface TypographyProps extends React.HTMLAttributes<HTMLElement> {
  as?: React.ElementType
  variant?: Variant
  muted?: boolean
}

const variants: Record<Variant, string[]> = {
  display: ['font-display text-5xl md:text-6xl tracking-tight'],
  h1: ['font-sans text-4xl md:text-5xl font-bold'],
  h2: ['font-sans text-3xl md:text-4xl font-bold'],
  h3: ['font-sans text-2xl md:text-3xl font-semibold'],
  h4: ['font-sans text-xl md:text-2xl font-semibold'],
  h5: ['font-sans text-lg font-medium'],
  h6: ['font-sans text-base font-medium'],
  body: ['font-sans text-base leading-relaxed'],
  caption: ['font-sans text-xs leading-normal'],
  code: ['font-mono text-sm'],
}

export function Typography({
  as = 'p',
  variant = 'body',
  className,
  children,
  muted = false,
  ...props
}: TypographyProps) {
  const Component = as as any
  return (
    <Component
      className={cn(
        variants[variant],
        muted ? 'text-neutral-600' : 'text-neutral-900',
        'antialiased',
        className,
      )}
      {...props}
    >
      {children}
    </Component>
  )
}

export default Typography
