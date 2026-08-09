import { cn } from '../utils'

interface ProgressBarProps {
  value: number
  className?: string
  color?: string
  showLabel?: boolean
}

export default function ProgressBar({ value, className, color = 'from-brand-600 to-purple-500', showLabel = true }: ProgressBarProps) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-500`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
      {showLabel && <span className="text-sm text-gray-500 w-10 text-right">{value}%</span>}
    </div>
  )
}