import { cn } from '../utils'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  className?: string
  onClick?: () => void
  type?: 'button' | 'submit'
}

export default function Button({ children, variant = 'primary', className, onClick, type = 'button' }: ButtonProps) {
  const styles = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm',
    secondary: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50',
    ghost: 'text-gray-600 hover:bg-gray-100',
  }
  return (
    <button type={type} onClick={onClick} className={cn(
      'inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-colors',
      styles[variant], className
    )}>
      {children}
    </button>
  )
}
