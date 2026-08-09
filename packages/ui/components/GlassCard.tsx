import { cn } from '../utils'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export default function GlassCard({ children, className, hover = true }: GlassCardProps) {
  return (
    <div className={cn(
      'bg-white/80 backdrop-blur-xl border border-white/60 rounded-2xl shadow-lg',
      hover && 'hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300',
      className
    )}>
      {children}
    </div>
  )
}