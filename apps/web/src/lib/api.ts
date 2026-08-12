/**
 * EduFlow 前端 API 客户端
 *
 * - 所有请求通过 Next.js rewrites 代理到后端 (http://localhost:8000/api/*)
 * - 自动附加 Authorization: Bearer <token>
 * - token 与用户信息存储在 localStorage
 */
import { STORAGE_KEYS } from './constants'

/* -------------------------------------------------------------------------- */
/*                                   类型定义                                  */
/* -------------------------------------------------------------------------- */

export interface User {
  id: number
  email: string
  username: string
  display_name?: string
  avatar_url?: string
  bio?: string
  is_active?: boolean
  is_verified?: boolean
  settings?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LearningPath {
  id: number
  user_id?: number
  title: string
  description?: string
  goal?: string
  estimated_duration?: number
  difficulty: string
  status: string
  progress: number
  modules?: Module[]
  created_at?: string
  updated_at?: string
}

export interface Module {
  id: number
  path_id: number
  title: string
  description?: string
  order: number
  content?: unknown[]
  status: string
  progress: number
  estimated_minutes?: number
  created_at?: string
}

export interface PathWithModules {
  path: LearningPath
  modules: Module[]
}

export interface Question {
  id: number
  type?: string
  question: string
  options?: string[]
  /** 正确选项的数字索引（字符串或数字） */
  answer: string | number
  explanation?: string
  difficulty?: string
  topic?: string
}

export interface PracticeSession {
  id: number
  user_id?: number
  module_id?: number
  session_type?: string
  questions?: Question[]
  answers?: Array<{ question_id: number; answer: string; is_correct: boolean }>
  score?: number
  status: string
  started_at?: string
  completed_at?: string
}

export interface SubmitAnswerPayload {
  session_id: number
  question_id: number
  answer: string
  is_correct: boolean
}

export interface SubmitAnswerResponse {
  score: number
  total: number
  correct: number
}

export interface ProgressRecord {
  id: number
  user_id: number
  module_id: number
  learning_time_minutes: number
  completion_percentage: number
  quiz_scores: number[]
  weak_points: string[]
  strong_points: string[]
  updated_at?: string
}

export interface ProgressDetail {
  module_id: number
  completion: number
  learning_time: number
}

export interface ProgressOverview {
  overall_completion: number
  module_count: number
  weak_points: string[]
  strong_points?: string[]
  details?: ProgressDetail[]
}

export interface AIChatResponse {
  response: string
  agent_type?: string
}

export interface AIExplainResponse {
  response: string
  topic: string
}

export interface AIGenerateQuestionsResponse {
  questions: Question[]
  count: number
}

export interface AIEvaluateResponse {
  is_correct: boolean
  score: number
  feedback: string
  hint?: string
}

export interface AIPlanResponse {
  goal?: string
  modules?: Array<{
    title: string
    description?: string
    estimated_minutes?: number
    difficulty?: string
  }>
  [key: string]: unknown
}

/* -------------------------------------------------------------------------- */
/*                                鉴权信息存储                                 */
/* -------------------------------------------------------------------------- */

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(STORAGE_KEYS.TOKEN)
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEYS.TOKEN, token)
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(STORAGE_KEYS.USER)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function setStoredUser(user: User): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
}

export function clearAuth(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(STORAGE_KEYS.TOKEN)
  localStorage.removeItem(STORAGE_KEYS.USER)
}

/* -------------------------------------------------------------------------- */
/*                                  请求核心                                   */
/* -------------------------------------------------------------------------- */

/** API 错误 */
export class ApiError extends Error {
  status: number
  detail?: unknown
  constructor(message: string, status: number, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

interface RequestOptions extends RequestInit {
  /** 是否跳过 JSON 解析（如 DELETE 可能无返回体） */
  skipJson?: boolean
  /** 超时毫秒数；超时抛出 ApiError(超时) */
  timeoutMs?: number
}

/**
 * 统一请求方法，自动附加 Authorization header
 */
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // 支持超时：通过 AbortController 中断慢请求，避免界面长期"加载中"
  let controller: AbortController | undefined
  let timeoutId: ReturnType<typeof setTimeout> | undefined
  if (options.timeoutMs) {
    controller = new AbortController()
    timeoutId = setTimeout(() => controller!.abort(), options.timeoutMs)
  }

  let res: Response
  try {
    res = await fetch(`/api${path}`, {
      ...options,
      headers,
      signal: controller?.signal,
    })
  } catch (e) {
    if (controller?.signal.aborted) {
      throw new ApiError(`请求超时(${Math.round((options.timeoutMs || 0) / 1000)}s)`, 408, e)
    }
    throw new ApiError('网络连接失败，请检查后端服务是否启动', 0, e)
  } finally {
    if (timeoutId) clearTimeout(timeoutId)
  }

  if (!res.ok) {
    let message = `请求失败 (${res.status})`
    let detail: unknown
    try {
      const data = await res.json()
      detail = data
      message = data.detail || data.message || data.error || message
    } catch {
      /* 无 JSON 体 */
    }
    throw new ApiError(message, res.status, detail)
  }

  if (options.skipJson || res.status === 204) {
    const text = await res.text()
    return (text ? JSON.parse(text) : null) as T
  }

  const text = await res.text()
  return text ? (JSON.parse(text) as T) : (null as unknown as T)
}

/* -------------------------------------------------------------------------- */
/*                                  API 模块                                  */
/* -------------------------------------------------------------------------- */

/** 鉴权 API */
export const authAPI = {
  login: (email: string, password: string) =>
    request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (data: { email: string; username: string; password: string; display_name?: string }) =>
    request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () => request<User>('/auth/me'),

  updateMe: (data: Partial<Pick<User, 'display_name' | 'bio' | 'avatar_url'>>) =>
    request<User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
}

/** 学习路径 / 模块 API */
export const learningAPI = {
  getPaths: () => request<LearningPath[]>('/learning/paths'),

  getPath: (id: number) => request<PathWithModules>(`/learning/paths/${id}`),

  createPath: (data: { title: string; description?: string; goal?: string; difficulty?: string }) =>
    request<LearningPath>('/learning/paths', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updatePath: (id: number, data: Partial<LearningPath>) =>
    request<LearningPath>(`/learning/paths/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deletePath: (id: number) =>
    request<void>(`/learning/paths/${id}`, { method: 'DELETE', skipJson: true }),

  getModule: (id: number) => request<Module>(`/learning/modules/${id}`),

  createModule: (data: { path_id: number; title: string; description?: string; order?: number; content?: unknown[] }) =>
    request<Module>('/learning/modules', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateModule: (id: number, data: Partial<Module>) =>
    request<Module>(`/learning/modules/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteModule: (id: number) =>
    request<void>(`/learning/modules/${id}`, { method: 'DELETE', skipJson: true }),
}

/** 练习 API */
export const practiceAPI = {
  getSessions: () => request<PracticeSession[]>('/practice/sessions'),

  getSession: (id: number) => request<PracticeSession>(`/practice/sessions/${id}`),

  createSession: (moduleId: number, sessionType = 'quiz', topic?: string, questions?: Question[]) =>
    request<PracticeSession>('/practice/sessions', {
      method: 'POST',
      body: JSON.stringify({ module_id: moduleId, session_type: sessionType, topic, questions }),
    }),

  deleteSession: (id: number) =>
    request<void>(`/practice/sessions/${id}`, { method: 'DELETE', skipJson: true }),

  submitAnswer: (data: SubmitAnswerPayload) =>
    request<SubmitAnswerResponse>('/practice/submit', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  completeSession: (id: number, weakPoints: string[] = [], strongPoints: string[] = []) =>
    request<PracticeSession>(`/practice/sessions/${id}/complete`, {
      method: 'PUT',
      body: JSON.stringify({ weak_points: weakPoints, strong_points: strongPoints }),
    }),
}

/** 进度 API */
export const progressAPI = {
  getMyProgress: () => request<ProgressOverview>('/progress/me'),

  updateProgress: (data: { module_id: number; learning_time_minutes?: number; completion_percentage?: number }) =>
    request<ProgressRecord>('/progress/update', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getOverview: () => request<ProgressOverview>('/progress/overview'),
}

/** 间隔重复复习项 */
export interface ReviewItem {
  id: number
  module_id?: number | null
  topic: string
  mastery_level: number
  review_count: number
  last_score?: number | null
  stability: number
  difficulty: number
  due_at?: string | null
  last_reviewed_at?: string | null
  status: 'due' | 'upcoming'
}

export interface ReviewDue {
  due_count: number
  upcoming_count: number
  total: number
  due_items: ReviewItem[]
  upcoming_items: ReviewItem[]
}

/** 复习 API */
export const reviewAPI = {
  getDue: () => request<ReviewDue>('/review/due'),

  getAll: () => request<{ items: ReviewItem[] }>('/review/'),

  submitReview: (id: number, score: number) =>
    request<ReviewItem>(`/review/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ score }),
    }),
}

/** 服务端会话持久化 */
export interface Conversation {
  id: number
  agent_type: string
  title: string
  message_count: number
  last_message?: string
  created_at?: string
  updated_at?: string
}

export interface ConversationMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

export interface ConversationDetail extends Conversation {
  messages: ConversationMessage[]
}

/** 会话 API */
export const conversationAPI = {
  list: () => request<{ conversations: Conversation[] }>('/conversations'),

  create: (agentType: 'tutor' | 'buddy', title = '') =>
    request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify({ agent_type: agentType, title }),
    }),

  get: (id: number) => request<ConversationDetail>(`/conversations/${id}`),

  remove: (id: number) =>
    request<void>(`/conversations/${id}`, { method: 'DELETE', skipJson: true }),

  appendMessage: (id: number, role: 'user' | 'assistant', content: string) =>
    request<ConversationMessage>(`/conversations/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify({ role, content }),
    }),
}

/** AI API */
export const aiAPI = {
  chat: (
    message: string,
    agentType: 'tutor' | 'buddy' = 'tutor',
    context: Record<string, unknown> = {},
    history: Array<{ role: 'user' | 'assistant'; content: string }> = []
  ) =>
    request<AIChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, agent_type: agentType, context, history }),
    }),

  generateQuestions: (topic: string, difficulty = 'medium', count = 5, context = '') =>
    request<AIGenerateQuestionsResponse>('/ai/generate-questions', {
      method: 'POST',
      body: JSON.stringify({ topic, difficulty, count, context }),
    }),

  explain: (concept: string, detailLevel = 'beginner', context: Record<string, unknown> = {}) =>
    request<AIExplainResponse>('/ai/explain', {
      method: 'POST',
      body: JSON.stringify({ concept, detail_level: detailLevel, context }),
    }),

  evaluate: (question: string, userAnswer: string, correctAnswer: string, context: Record<string, unknown> = {}) =>
    request<AIEvaluateResponse>('/ai/evaluate', {
      method: 'POST',
      body: JSON.stringify({ question, user_answer: userAnswer, correct_answer: correctAnswer, context }),
    }),

  plan: (
    goal: string,
    level = 'beginner',
    durationWeeks = 4,
    difficulty = 'medium',
    context: Record<string, unknown> = {}
  ) =>
    request<AIPlanResponse>('/ai/plan', {
      method: 'POST',
      body: JSON.stringify({ goal, level, duration_weeks: durationWeeks, difficulty, context }),
    }),

  /** 知识库检索工具 */
  knowledge: (query: string, topic = '', includePrerequisites = false) =>
    request<{ knowledge: string; prerequisites: string; has_results: boolean }>('/ai/knowledge', {
      method: 'POST',
      body: JSON.stringify({ query, topic, include_prerequisites: includePrerequisites }),
    }),

  /** 流式对话(SSE)：通过 onDelta 回调接收增量文本 */
  chatStream: (
    message: string,
    agentType: 'tutor' | 'buddy' = 'tutor',
    context: Record<string, unknown> = {},
    history: Array<{ role: 'user' | 'assistant'; content: string }> = [],
    onDelta: (delta: string) => void
  ) => {
    const token = getToken()
    return fetch('/api/ai/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, agent_type: agentType, context, history }),
    }).then(async res => {
      if (!res.ok || !res.body) throw new Error('流式连接失败')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let idx = buffer.indexOf('\n\n')
        while (idx >= 0) {
          const event = buffer.slice(0, idx)
          buffer = buffer.slice(idx + 2)
          const lines = event.split('\n').filter(l => l.startsWith('data: '))
          for (const line of lines) {
            const data = line.slice(6)
            if (data === '[done]') return
            if (data.startsWith('[error]')) throw new Error(data.slice(7))
            onDelta(data)
          }
          idx = buffer.indexOf('\n\n')
        }
      }
    })
  },
}

/** 保留兼容旧调用 */
export async function apiFetch(path: string, options?: RequestInit) {
  const token = getToken()
  const res = await fetch(`/api${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
