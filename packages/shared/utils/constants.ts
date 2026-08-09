export const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: '入门',
  easy: '简单',
  medium: '中等',
  hard: '困难',
  expert: '专家',
}

export const MODULE_STATUS_LABELS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
}

export const PATH_STATUS_LABELS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
}

export const AI_AGENTS = [
  { type: 'tutor' as const, name: 'AI 导师', icon: '🎓', description: '按需辅导答疑，苏格拉底式教学' },
  { type: 'buddy' as const, name: 'AI 伴学', icon: '🤝', description: '协同练习对话，像同学一样讨论' },
  { type: 'examiner' as const, name: 'AI 出题者', icon: '📝', description: '自适应出题，即时反馈解析' },
  { type: 'planner' as const, name: 'AI 规划师', icon: '🎯', description: '个性化学习路径规划' },
]

export const API_ENDPOINTS = {
  api: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  ai: process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8100',
  engine: process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8200',
} as const