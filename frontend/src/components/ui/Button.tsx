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
        'bg-blue-600 text-white hover:bg-blue-700',
        'focus:ring-blue-500',
        'shadow-md hover:shadow-lg',
        gradient && 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800'
      ],
      secondary: [
        'bg-gray-100 text-gray-900 hover:bg-gray-200',
        'focus:ring-gray-500',
        'border border-gray-300',
      ],
      accent: [
        'bg-purple-600 text-white hover:bg-purple-700',
        'focus:ring-purple-500',
        'shadow-lg hover:shadow-xl',
        gradient && 'bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700'
      ],
      success: [
        'bg-green-600 text-white hover:bg-green-700',
        'focus:ring-green-500',
        gradient && 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700'
      ],
      warning: [
        'bg-yellow-600 text-white hover:bg-yellow-700',
        'focus:ring-yellow-500',
        gradient && 'bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700'
      ],
      danger: [
        'bg-red-600 text-white hover:bg-red-700',
        'focus:ring-red-500',
        gradient && 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700'
      ],
      ghost: [
        'text-gray-700 hover:bg-gray-100',
        'focus:ring-gray-500',
      ],
      outline: [
        'border-2 border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white',
        'focus:ring-blue-500',
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