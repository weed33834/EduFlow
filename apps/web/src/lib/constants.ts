/**
 * EduFlow 前端常量定义
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const AI_API_BASE = process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8100'

/** 难度标签映射 */
export const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: '入门',
  easy: '简单',
  medium: '中等',
  hard: '困难',
  expert: '专家',
  intermediate: '中等',
  advanced: '高级',
}

/** 模块状态映射（与后端一致） */
export const MODULE_STATUS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
}

/** 学习路径状态映射（与后端一致） */
export const PATH_STATUS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
}

/** 难度等级（含颜色，用于标签） */
export const DIFFICULTY_LEVELS = [
  { value: 'beginner', label: '入门', color: 'bg-green-100 text-green-700' },
  { value: 'easy', label: '简单', color: 'bg-blue-100 text-blue-700' },
  { value: 'medium', label: '中等', color: 'bg-amber-100 text-amber-700' },
  { value: 'hard', label: '困难', color: 'bg-red-100 text-red-700' },
  { value: 'expert', label: '专家', color: 'bg-purple-100 text-purple-700' },
] as const

/** 难度可选项（用于表单下拉） */
export const DIFFICULTY_OPTIONS = DIFFICULTY_LEVELS.map(d => ({ value: d.value, label: d.label }))

/** AI 智能体配置 */
export const AI_AGENTS = [
  { id: 'tutor', name: 'AI 导师', icon: 'tutor', desc: '按需辅导答疑' },
  { id: 'buddy', name: 'AI 伴学', icon: 'buddy', desc: '协同练习对话' },
  { id: 'examiner', name: 'AI 出题者', icon: 'examiner', desc: '自适应出题' },
] as const

/** localStorage 键名 */
export const STORAGE_KEYS = {
  TOKEN: 'eduflow_token',
  USER: 'eduflow_user',
} as const

/** AI 导师快捷问题 */
export const TUTOR_QUICK_QUESTIONS = [
  '如何高效制定学习计划？',
  '解释一下什么是递归？',
  'Python 列表和元组有什么区别？',
  '怎样提高我的专注力？',
]

/** AI 伴学快捷问题 */
export const BUDDY_QUICK_QUESTIONS = [
  '陪我一起复习今天的知识点吧',
  '我们来做个小测验吧',
  '我今天有点不想学习，怎么办？',
  '给我讲个学习相关的小故事吧',
]
