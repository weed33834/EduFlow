/**
 * EduAgent 前端 API 客户端
 *
 * 直连后端（不走 Next.js rewrites，避免 SSE 超时）
 * 支持流式 SSE：status → stream → complete → [done]
 */
import { API_BASE, STORAGE_KEYS } from './constants'

const API_ROOT = `${API_BASE}/api`

/* ─────────────────── 类型定义 ─────────────────── */

export interface User {
  id: number
  email: string
  username: string
  display_name?: string
  bio?: string
  avatar_url?: string
  created_at?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface SessionSummary {
  id: number
  started_at: string | null
  ended_at: string | null
  message_count: number
  last_message: string | null
}

export interface Message {
  id: number
  role: string
  content: string
  created_at: string | null
}

export interface SessionDetail {
  id: number
  started_at: string | null
  messages: Message[]
}

export interface QuizData {
  question: string
  options: string[]
  answer: number
  explanation: string
  difficulty?: string
}

export interface CodeResult {
  success: boolean
  stdout: string
  stderr: string
  exit_code: number
}

/* ─────────────────── 认证存储 ─────────────────── */

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

/* ─────────────────── 请求核心 ─────────────────── */

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(`${API_ROOT}${path}`, { ...options, headers })
  } catch (e) {
    throw new ApiError('网络连接失败，请检查后端服务是否启动', 0)
  }

  if (!res.ok) {
    let message = `请求失败 (${res.status})`
    try {
      const data = await res.json()
      message = data.detail || data.message || message
    } catch {
      /* 无 JSON 体 */
    }
    throw new ApiError(message, res.status)
  }

  const text = await res.text()
  return text ? (JSON.parse(text) as T) : (null as unknown as T)
}

/* ─────────────────── API 模块 ─────────────────── */

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

export const sessionAPI = {
  list: () => request<SessionSummary[]>('/sessions'),
  get: (id: number) => request<SessionDetail>(`/sessions/${id}`),
  remove: (id: number) =>
    request<{ ok: boolean }>(`/sessions/${id}`, { method: 'DELETE' }),
}

export const profileAPI = {
  get: () =>
    request<{
      current_level: string
      learning_goal: string | null
      preferred_style: string
      strengths: string[]
      weaknesses: string[]
      total_study_minutes: number
      streak_days: number
    }>('/profile'),
  update: (data: { learning_goal?: string; current_level?: string; preferred_style?: string }) =>
    request('/profile', { method: 'PUT', body: JSON.stringify(data) }),
}

/* ─────────────────── 重试工具 ─────────────────── */

async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000,
): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn()
    } catch (err) {
      if (i === maxRetries) throw err
      const delay = Math.min(baseDelay * Math.pow(2, i), 10000)
      await new Promise((r) => setTimeout(r, delay))
    }
  }
  throw new Error('重试次数耗尽')
}

/* ─────────────────── 对话（SSE 流式） ─────────────────── */

export interface ChatResponseData {
  type: 'status' | 'stream' | 'message' | 'quiz' | 'complete'
  content: string
  session_id?: number
  quiz?: QuizData
  code_result?: CodeResult
}

export async function chatStream(
  message: string,
  sessionId: number | null,
  onEvent: (data: ChatResponseData) => void,
  onError: (err: Error) => void,
) {
  const token = getToken()
  try {
    const res = await retryWithBackoff(() => fetch(`${API_ROOT}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    }))

    if (!res.ok || !res.body) {
      const errText = await res.text().catch(() => '')
      throw new Error(errText || `请求失败 (${res.status})`)
    }

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
        const lines = event.split('\n').filter((l) => l.startsWith('data: '))
        for (const line of lines) {
          const data = line.slice(6)
          if (data === '[done]') return
          if (data.startsWith('[error]')) {
            throw new Error(data.slice(7))
          }
          try {
            const parsed = JSON.parse(data) as ChatResponseData
            onEvent(parsed)
          } catch {
            /* 忽略解析失败 */
          }
        }
        idx = buffer.indexOf('\n\n')
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error('对话失败'))
  }
}
