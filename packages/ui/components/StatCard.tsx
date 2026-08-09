import { cn } from '../utils'

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  change?: string
  color?: string
  className?: string
}

export default function StatCard({ icon, label, value, change, color = 'bg-brand-600', className }: StatCardProps) {
  return (
    <div className={cn('bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-5', className)}>
      <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-3', color)}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="flex items-center justify-between mt-1">
        <span className="text-sm text-gray-500">{label}</span>
        {change && <span className="text-xs text-green-600 font-medium">{change}</span>}
      </div>
    </div>
  )
}