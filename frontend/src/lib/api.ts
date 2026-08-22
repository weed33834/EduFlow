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
  title?: string | null
  pinned?: boolean
  archived?: boolean
  started_at: string | null
  ended_at: string | null
  message_count: number
  last_message: string | null
}

export interface Message {
  id: number
  role: string
  content: string
  metadata?: Record<string, unknown> | null
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
  /** 历史消息里已作答的题带此标记（后端持久化） */
  answered?: boolean
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
  list: (archived = false) =>
    request<SessionSummary[]>(`/sessions${archived ? '?archived=true' : ''}`),
  get: (id: number) => request<SessionDetail>(`/sessions/${id}`),
  remove: (id: number) =>
    request<{ ok: boolean }>(`/sessions/${id}`, { method: 'DELETE' }),
  update: (
    id: number,
    data: { summary?: string; pinned?: boolean; archived?: boolean },
  ) =>
    request<{ ok: boolean; summary: string | null; pinned: boolean; archived: boolean }>(
      `/sessions/${id}`,
      { method: 'PATCH', body: JSON.stringify(data) },
    ),
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
      // 用户主动取消不重试
      if (err instanceof DOMException && err.name === 'AbortError') throw err
      if (i === maxRetries) throw err
      const delay = Math.min(baseDelay * Math.pow(2, i), 10000)
      await new Promise((r) => setTimeout(r, delay))
    }
  }
  throw new Error('重试次数耗尽')
}

/* ─────────────────── 对话（SSE 流式） ─────────────────── */

export interface ToolTraceItem {
  tool: string
  round?: number
  dur_ms?: number
  ok?: boolean
}

export interface JudgedSummary {
  mode: 'quiz' | 'review'
  correct: boolean
  /** 仅 quiz 模式：学生所选与正确选项索引（用于回显对错高亮） */
  selected?: number | null
  answer?: number | null
}

export interface ChatResponseData {
  type: 'status' | 'stream' | 'complete'
  content: string
  session_id?: number
  quiz?: QuizData
  code_result?: CodeResult
  judged?: JudgedSummary
  tool_trace?: ToolTraceItem[]
}

/* ─────────────────── 幂等键 ─────────────────── */

export function newRequestId(): string {
  // crypto.randomUUID 仅在安全上下文可用；局域网 http 部署时回退
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`
}

/** 通用 SSE 对话流：chat / regenerate / edit 共用 */
async function streamChatSSE(
  body: Record<string, unknown>,
  onEvent: (data: ChatResponseData) => void,
  onError: (err: Error) => void,
  signal?: AbortSignal,
  useRetry = false,
) {
  const token = getToken()
  const doFetch = () => fetch(`${API_ROOT}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  })

  try {
    const res = await (useRetry ? retryWithBackoff(doFetch) : doFetch())

    if (!res.ok || !res.body) {
      const errText = await res.text().catch(() => '')
      let message = errText || `请求失败 (${res.status})`
      // FastAPI 校验错误体是 {detail:[...]} 数组
      try {
        const parsed = JSON.parse(errText)
        if (Array.isArray(parsed.detail)) {
          message = parsed.detail.map((d: { msg?: string }) => d.msg || '').join('; ') || message
        } else if (typeof parsed.detail === 'string') {
          message = parsed.detail
        }
      } catch { /* 非 JSON 体，保留原文 */ }
      throw new Error(message)
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
    if (err instanceof DOMException && err.name === 'AbortError') return
    onError(err instanceof Error ? err : new Error('对话失败'))
  }
}

export async function chatStream(
  message: string,
  sessionId: number | null,
  onEvent: (data: ChatResponseData) => void,
  onError: (err: Error) => void,
  signal?: AbortSignal,
) {
  const requestId = newRequestId() // 同一次发送的所有重试共用，后端据此去重
  await streamChatSSE(
    { message, session_id: sessionId, request_id: requestId },
    onEvent, onError, signal, true, // 幂等键在，网络重试安全
  )
}

/** v0.6.0 重新生成：重跑会话最后一轮（不可自动重试） */
export async function regenerateStream(
  sessionId: number,
  onEvent: (data: ChatResponseData) => void,
  onError: (err: Error) => void,
  signal?: AbortSignal,
) {
  await streamChatSSE({ regenerate: true, session_id: sessionId }, onEvent, onError, signal)
}

/** v0.6.0 编辑用户消息并重发：后端截断其后消息、原位更新并重跑 */
export async function editResendStream(
  sessionId: number,
  messageId: number,
  newContent: string,
  onEvent: (data: ChatResponseData) => void,
  onError: (err: Error) => void,
  signal?: AbortSignal,
) {
  await streamChatSSE(
    { session_id: sessionId, message_id: messageId, new_content: newContent },
    onEvent, onError, signal,
  )
}
