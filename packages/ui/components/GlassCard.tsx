import { cn } from '../utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

/** 统一卡片容器：干净的实心卡片 */
export default function GlassCard({ children, className, hover = true }: CardProps) {
  return (
    <div className={cn(
      'bg-white border border-gray-200 rounded-2xl shadow-sm',
      hover && 'hover:shadow-md hover:border-gray-300 transition-all duration-200',
      className
    )}>
      {children}
    </div>
  )
}
