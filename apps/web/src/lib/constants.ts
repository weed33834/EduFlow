export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const AI_API_BASE = process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8100'

export const DIFFICULTY_LEVELS = [
  { value: 'beginner', label: '入门', color: 'bg-green-100 text-green-600' },
  { value: 'easy', label: '简单', color: 'bg-blue-100 text-blue-600' },
  { value: 'medium', label: '中等', color: 'bg-amber-100 text-amber-600' },
  { value: 'hard', label: '困难', color: 'bg-red-100 text-red-600' },
] as const

export const AI_AGENTS = [
  { id: 'tutor', name: 'AI 导师', icon: '🎓', desc: '按需辅导答疑' },
  { id: 'buddy', name: 'AI 伴学', icon: '🤝', desc: '协同练习对话' },
  { id: 'examiner', name: 'AI 出题者', icon: '📝', desc: '自适应出题' },
] as const