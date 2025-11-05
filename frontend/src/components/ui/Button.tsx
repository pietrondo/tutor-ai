import React from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'danger' | 'ghost' | 'outline'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  fullWidth?: boolean
  rounded?: boolean
  gradient?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = 'primary',
    size = 'md',
    loading = false,
    icon,
    iconPosition = 'left',
    fullWidth = false,
    rounded = false,
    gradient = false,
    children,
    disabled,
    ...props
  }, ref) => {
    const baseClasses = [
      'inline-flex items-center justify-center',
      'font-medium transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'relative overflow-hidden group',
    ]

    const variants = {
      primary: [
        'bg-primary-600 text-white hover:bg-primary-700',
        'focus:ring-primary-500',
        'shadow-medium hover:shadow-large',
        gradient && 'bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800'
      ],
      secondary: [
        'bg-neutral-100 text-neutral-900 hover:bg-neutral-200',
        'focus:ring-neutral-500',
        'border border-neutral-300',
      ],
      accent: [
        'bg-accent-600 text-white hover:bg-accent-700',
        'focus:ring-accent-500',
        'shadow-glow hover:shadow-glow-lg',
        gradient && 'bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700'
      ],
      success: [
        'bg-success-600 text-white hover:bg-success-700',
        'focus:ring-success-500',
        gradient && 'bg-gradient-to-r from-success-500 to-success-600 hover:from-success-600 hover:to-success-700'
      ],
      warning: [
        'bg-warning-600 text-white hover:bg-warning-700',
        'focus:ring-warning-500',
        gradient && 'bg-gradient-to-r from-warning-500 to-warning-600 hover:from-warning-600 hover:to-warning-700'
      ],
      danger: [
        'bg-danger-600 text-white hover:bg-danger-700',
        'focus:ring-danger-500',
        gradient && 'bg-gradient-to-r from-danger-500 to-danger-600 hover:from-danger-600 hover:to-danger-700'
      ],
      ghost: [
        'text-neutral-700 hover:bg-neutral-100',
        'focus:ring-neutral-500',
      ],
      outline: [
        'border-2 border-primary-600 text-primary-600 hover:bg-primary-600 hover:text-white',
        'focus:ring-primary-500',
      ],
    }

    const sizes = {
      xs: ['px-3 py-1.5 text-xs', 'rounded-md'],
      sm: ['px-4 py-2 text-sm', 'rounded-lg'],
      md: ['px-6 py-2.5 text-base', 'rounded-lg'],
      lg: ['px-8 py-3 text-lg', 'rounded-xl'],
      xl: ['px-10 py-4 text-xl', 'rounded-2xl'],
    }

    const classes = cn(
      baseClasses,
      variants[variant],
      sizes[size],
      fullWidth && 'w-full',
      rounded && 'rounded-full',
      gradient && variants[variant],
      className
    )

    const renderIcon = () => {
      if (loading) {
        return (
          <Loader2 className={cn(
            'animate-spin',
            iconPosition === 'left' ? 'mr-2' : 'ml-2',
            size === 'xs' ? 'h-3 w-3' :
            size === 'sm' ? 'h-4 w-4' :
            size === 'md' ? 'h-5 w-5' :
            size === 'lg' ? 'h-6 w-6' : 'h-7 w-7'
          )} />
        )
      }

      if (React.isValidElement<{ className?: string }>(icon)) {
        const iconElement = icon
        return React.cloneElement(iconElement, {
          ...iconElement.props,
          className: cn(
            iconElement.props?.className,
            iconPosition === 'left' ? 'mr-2' : 'ml-2',
            size === 'xs' ? 'h-3 w-3' :
            size === 'sm' ? 'h-4 w-4' :
            size === 'md' ? 'h-5 w-5' :
            size === 'lg' ? 'h-6 w-6' : 'h-7 w-7'
          )
        })
      }

      return null
    }

    return (
      <button
        className={classes}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {/* Shimmer effect for loading state */}
        {loading && (
          <div className="absolute inset-0 -top-2 -left-2 h-[calc(100%+16px)] w-[calc(100%+16px)]">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-[1.5s] ease-out repeat-infinite" />
          </div>
        )}

        {iconPosition === 'left' && renderIcon()}
        <span className={loading ? 'opacity-70' : ''}>{children}</span>
        {iconPosition === 'right' && renderIcon()}
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button }
