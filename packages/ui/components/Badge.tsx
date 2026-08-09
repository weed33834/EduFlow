import { cn } from '../utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  dot?: boolean
  className?: string
}

export default function Badge({ children, variant = 'default', dot = false, className }: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-amber-100 text-amber-700',
    error: 'bg-red-100 text-red-700',
    info: 'bg-brand-100 text-brand-700',
  }

  const dotColors = {
    default: 'bg-gray-400',
    success: 'bg-green-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500',
    info: 'bg-brand-500',
  }

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
      variants[variant], className
    )}>
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])} />}
      {children}
    </span>
  )
}
