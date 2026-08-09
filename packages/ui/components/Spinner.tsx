import { cn } from '../utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export default function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-[3px]',
    lg: 'w-12 h-12 border-4',
  }

  return (
    <div
      className={cn(
        'inline-block rounded-full border-gray-200 border-t-brand-600 animate-spin',
        sizes[size], className
      )}
      role="status"
      aria-label="加载中"
    />
  )
}
