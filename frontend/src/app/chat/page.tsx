'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Send, Sparkles, Loader2, Plus, Trash2, MessageSquare,
  LogOut, Menu, X, Brain, Terminal, Square, Copy, Check, RefreshCw, Pencil,
  ArrowDown, Download, Star, Archive, ArchiveRestore,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import ThemeToggle from '@/components/ThemeToggle'
import {
  chatStream, regenerateStream, editResendStream, sessionAPI,
  type ChatResponseData, type SessionSummary, type CodeResult, type QuizData,
  type JudgedSummary,
} from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn, formatDateTime } from '@/lib/utils'

interface ChatMsg {
  id?: number
  role: 'user' | 'assistant'
  content: string
  quiz?: QuizData
  codeResult?: CodeResult
  judged?: JudgedSummary
  timestamp: number
  error?: boolean
}

export default function ChatPage() {
  const router = useRouter()
  const { user, logout } = useAuth()

  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editValue, setEditValue] = useState('')
  const [sidebarTab, setSidebarTab] = useState<'all' | 'archived'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [editingMsgIdx, setEditingMsgIdx] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState('')

  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const followRef = useRef(true) // 用户上滑阅读时暂停自动跟随

  const [showScrollBtn, setShowScrollBtn] = useState(false)

  const scrollToBottom = useCallback((smooth = true) => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
    followRef.current = true
    setShowScrollBtn(false)
  }, [])

  const handleThreadScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120
    followRef.current = nearBottom
    setShowScrollBtn(!nearBottom)
  }, [])

  // 加载会话列表（按当前标签：全部 / 归档）
  const loadSessions = useCallback(async () => {
    try {
      const list = await sessionAPI.list(sidebarTab === 'archived')
      setSessions(list)
    } catch {
      setSessions([])
    } finally {
      setLoadingSessions(false)
    }
  }, [sidebarTab])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // 自动滚动：仅当用户本来就在底部（未上滑阅读历史）时跟随
  useEffect(() => {
    if (!followRef.current) return
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight })
  }, [messages, sending])

  // textarea 自动增高
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 128) + 'px'
  }, [input])

  const handleSelectSession = useCallback(async (id: number) => {
    setActiveSessionId(id)
    setSidebarOpen(false)
    try {
      const detail = await sessionAPI.get(id)
      setMessages(
      detail.messages.map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
        quiz: (m.metadata?.quiz ?? undefined) as QuizData | undefined,
        codeResult: (m.metadata?.code_result ?? undefined) as CodeResult | undefined,
        judged: (m.metadata?.judged ?? undefined) as JudgedSummary | undefined,
        timestamp: new Date(m.created_at || '').getTime(),
      })),
      )
    } catch {
      setMessages([])
    }
  }, [])

  const handleNewChat = useCallback(() => {
    setActiveSessionId(null)
    setMessages([])
    setSidebarOpen(false)
    inputRef.current?.focus()
  }, [])

  const handleStop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    setSending(false)
  }, [])

  const sendMessage = useCallback(
    async (text: string, retryTs?: number) => {
      const trimmed = text.trim()
      if (!trimmed || sending) return

      setInput('')
      setSending(true)

      const userTs = retryTs || Date.now()
      const assistantTs = userTs + 1

      // 如果是重试，替换错误消息；否则添加新消息
      if (retryTs) {
        setMessages((prev) => prev.map((m) =>
          m.timestamp === retryTs + 1
            ? { role: 'assistant', content: '', timestamp: assistantTs }
            : m,
        ))
      } else {
        const userMsg: ChatMsg = { role: 'user', content: trimmed, timestamp: userTs }
        const assistantMsg: ChatMsg = { role: 'assistant', content: '', timestamp: assistantTs }
        setMessages((prev) => [...prev, userMsg, assistantMsg])
      }

      const controller = new AbortController()
      abortRef.current = controller

      await chatStream(
        trimmed,
        activeSessionId,
        (data: ChatResponseData) => {
          if (data.type === 'status') return
          if (data.type === 'stream') {
            setMessages((prev) =>
              prev.map((m) =>
                m.timestamp === assistantTs
                  ? { ...m, content: m.content + data.content }
                  : m,
              ),
            )
            return
          }
          // type === 'complete'
          setMessages((prev) =>
            prev.map((m) =>
              m.timestamp === assistantTs
                ? {
                    role: 'assistant',
                    content: data.content,
                    quiz: data.quiz,
                    codeResult: data.code_result,
                    judged: data.judged,
                    timestamp: assistantTs,
                  }
                : m,
            ),
          )
          if (data.session_id && !activeSessionId) {
            setActiveSessionId(data.session_id)
          }
        },
        (err: Error) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.timestamp === assistantTs
                ? {
                    role: 'assistant',
                    content: err.message,
                    timestamp: assistantTs,
                    error: true,
                  }
                : m,
            ),
          )
        },
        controller.signal,
      )

      abortRef.current = null
      loadSessions()
      setSending(false)
      inputRef.current?.focus()
    },
    [sending, activeSessionId, loadSessions],
  )

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleDeleteSession = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await sessionAPI.remove(id)
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (activeSessionId === id) {
        handleNewChat()
      }
    } catch {
      /* best effort */
    }
  }

  const startRename = (s: SessionSummary, e: React.SyntheticEvent) => {
    e.stopPropagation()
    setEditingId(s.id)
    setEditValue(s.title || s.last_message || '')
  }

  const commitRename = useCallback(async () => {
    const id = editingId
    setEditingId(null)
    if (!id) return
    const title = editValue.trim()
    if (!title) return
    try {
      await sessionAPI.update(id, { summary: title })
      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, title } : s)),
      )
    } catch {
      /* best effort */
    }
  }, [editingId, editValue])

  // 用服务端数据刷新当前会话消息（拿回 DB id 与最新状态）
  const refreshThread = useCallback(async (sid: number) => {
    try {
      const detail = await sessionAPI.get(sid)
      setMessages(
        detail.messages.map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          quiz: (m.metadata?.quiz ?? undefined) as QuizData | undefined,
          codeResult: (m.metadata?.code_result ?? undefined) as CodeResult | undefined,
          judged: (m.metadata?.judged ?? undefined) as JudgedSummary | undefined,
          timestamp: new Date(m.created_at || '').getTime(),
        })),
      )
    } catch {
      /* best effort */
    }
  }, [])

  // v0.6.0 重新生成最后一轮回复
  const handleRegenerate = useCallback(async () => {
    if (!activeSessionId || sending) return
    setSending(true)
    setInput('')
    const assistantTs = Date.now()
    // 移除本地最后一条助手消息，等待流式重写
    setMessages((prev) => {
      const arr = [...prev]
      while (arr.length && arr[arr.length - 1].role === 'assistant') arr.pop()
      return [...arr, { role: 'assistant', content: '', timestamp: assistantTs }]
    })
    const controller = new AbortController()
    abortRef.current = controller

    await regenerateStream(
      activeSessionId,
      (data) => {
        if (data.type === 'stream') {
          setMessages((prev) =>
            prev.map((m) =>
              m.timestamp === assistantTs ? { ...m, content: m.content + data.content } : m,
            ),
          )
        } else if (data.type === 'complete') {
          setMessages((prev) =>
            prev.map((m) =>
              m.timestamp === assistantTs
                ? {
                    ...m,
                    content: data.content,
                    quiz: data.quiz,
                    codeResult: data.code_result,
                    judged: data.judged,
                  }
                : m,
            ),
          )
        }
      },
      (err) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.timestamp === assistantTs
              ? { ...m, content: err.message, error: true }
              : m,
          ),
        )
      },
      controller.signal,
    )
    abortRef.current = null
    if (activeSessionId) await refreshThread(activeSessionId)
    setSending(false)
  }, [activeSessionId, sending, refreshThread])

  // v0.6.0 编辑用户消息并重发
  const startEditMessage = useCallback((idx: number) => {
    setEditingMsgIdx(idx)
    setEditDraft(messages[idx]?.content ?? '')
  }, [messages])

  const commitEditMessage = useCallback(async () => {
    const idx = editingMsgIdx
    setEditingMsgIdx(null)
    if (idx == null || !activeSessionId || sending) return
    const target = messages[idx]
    if (!target?.id) return
    const draft = editDraft.trim()
    if (!draft || draft === target.content) return

    setSending(true)
    // 本地立即呈现：截断其后并替换文本，等待重跑结果
    setMessages((prev) => [
      ...prev.slice(0, idx),
      { ...target, content: draft },
      { role: 'assistant' as const, content: '', timestamp: Date.now() },
    ])

    await editResendStream(
      activeSessionId, target.id, draft,
      (data) => {
        if (data.type === 'stream') {
          setMessages((prev) =>
            prev.map((m, i) =>
              i === prev.length - 1 && m.role === 'assistant'
                ? { ...m, content: m.content + data.content }
                : m,
            ),
          )
        } else if (data.type === 'complete') {
          setMessages((prev) =>
            prev.map((m, i) =>
              i === prev.length - 1 && m.role === 'assistant'
                ? { ...m, content: data.content, quiz: data.quiz,
                    codeResult: data.code_result, judged: data.judged }
                : m,
            ),
          )
        }
      },
      (err) => {
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 && m.role === 'assistant'
              ? { ...m, content: err.message, error: true }
              : m,
          ),
        )
      },
    )
    if (activeSessionId) await refreshThread(activeSessionId)
    setSending(false)
  }, [editingMsgIdx, messages, activeSessionId, sending, editDraft, refreshThread])

  // 置顶 / 归档切换
  const togglePin = useCallback(async (s: SessionSummary, e: React.SyntheticEvent) => {
    e.stopPropagation()
    try {
      const next = !s.pinned
      await sessionAPI.update(s.id, { pinned: next })
      setSessions((prev) => prev.map((x) => (x.id === s.id ? { ...x, pinned: next } : x)))
    } catch { /* best effort */ }
  }, [])

  const toggleArchive = useCallback(async (s: SessionSummary, e: React.SyntheticEvent) => {
    e.stopPropagation()
    try {
      const next = !s.archived
      await sessionAPI.update(s.id, { archived: next })
      setSessions((prev) => prev.filter((x) => x.id !== s.id))
      if (activeSessionId === s.id) handleNewChat()
    } catch { /* best effort */ }
  }, [activeSessionId, handleNewChat])

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const exportMarkdown = useCallback(() => {
    if (messages.length === 0) return
    const title = sessions.find((s) => s.id === activeSessionId)?.title || 'EduAgent 对话'
    const lines: string[] = [`# ${title}`, '']
    for (const m of messages) {
      const who = m.role === 'user' ? '🙋 我' : '🤖 EduAgent'
      lines.push(`### ${who}`)
      lines.push('')
      lines.push(m.content)
      lines.push('')
    }
    lines.push('---', `*导出于 ${new Date().toLocaleString('zh-CN')} · EduAgent*`)
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${title.replace(/[\\/:*?"<>|]/g, '_').slice(0, 40)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }, [messages, sessions, activeSessionId])

  const showQuickQuestions = messages.length === 0

  return (
    <div className="h-screen flex overflow-hidden">
      {/* 侧边栏 */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 flex flex-col transition-transform duration-300',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        <div className="flex items-center justify-between p-3 border-b border-gray-100">
          <span className="text-sm font-bold text-gray-700">对话历史</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3 space-y-2">
          <button
            onClick={handleNewChat}
            className="btn-primary w-full !py-2 text-sm"
          >
            <Plus className="w-4 h-4" /> 新对话
          </button>

          {/* 全部 / 归档 标签 */}
          <div
            className="flex gap-1 p-1 rounded-xl text-xs"
            style={{ backgroundColor: 'var(--surface-sunken)' }}
          >
            {([['all', '全部'], ['archived', '归档']] as const).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setSidebarTab(key)}
                className={cn(
                  'flex-1 py-1.5 rounded-lg font-medium transition-all',
                  sidebarTab === key
                    ? 'bg-white shadow-sm text-brand-600 dark:bg-slate-700 dark:text-brand-300'
                    : 'text-gray-500 hover:text-gray-700',
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {/* 搜索 */}
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索对话..."
            className="input-field !py-2 !text-xs"
          />
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-1">
          {loadingSessions ? (
            <div className="text-center py-4 text-sm text-gray-400">加载中...</div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-400">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
              {sidebarTab === 'archived' ? '暂无归档对话' : '还没有对话'}
            </div>
          ) : (
            sessions
              .filter((s) => {
                const q = searchQuery.trim().toLowerCase()
                if (!q) return true
                return (
                  (s.title || '').toLowerCase().includes(q) ||
                  (s.last_message || '').toLowerCase().includes(q)
                )
              })
              .map((s) => (
              editingId === s.id ? (
                <div key={s.id} className="px-1 py-1">
                  <input
                    autoFocus
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') commitRename()
                      if (e.key === 'Escape') setEditingId(null)
                    }}
                    onBlur={commitRename}
                    className="w-full px-2.5 py-2 rounded-lg text-sm bg-white border border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/60 dark:bg-slate-900"
                    maxLength={60}
                  />
                </div>
              ) : (
              <button
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
              className={cn(
                'w-full text-left px-3 py-2.5 rounded-xl transition-all duration-150 group',
                activeSessionId === s.id
                  ? 'bg-brand-50/80 text-brand-700 ring-1 ring-brand-200 shadow-sm dark:bg-brand-600/10 dark:text-brand-300 dark:ring-brand-500/30'
                  : 'hover:bg-gray-100/70 text-gray-600',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium truncate flex-1 flex items-center gap-1">
                  {s.pinned && (
                    <Star className="w-3 h-3 text-amber-400 fill-amber-400 flex-shrink-0" />
                  )}
                  <span className="truncate">
                    {s.title || s.last_message || `对话 #${s.id}`}
                  </span>
                </span>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => startRename(s, e)}
                  onKeyDown={(e) => e.key === 'Enter' && startRename(s, e)}
                  className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-brand-600 transition-opacity cursor-pointer flex-shrink-0"
                  title="重命名"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </span>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => togglePin(s, e)}
                  onKeyDown={(e) => e.key === 'Enter' && togglePin(s, e)}
                  className={cn(
                    'transition-opacity cursor-pointer flex-shrink-0',
                    s.pinned
                      ? 'text-amber-400'
                      : 'opacity-0 group-hover:opacity-100 text-gray-300 hover:text-amber-400',
                  )}
                  title={s.pinned ? '取消置顶' : '置顶'}
                >
                  <Star className="w-3.5 h-3.5" />
                </span>
                {sidebarTab === 'archived' ? (
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => toggleArchive(s, e)}
                    onKeyDown={(e) => e.key === 'Enter' && toggleArchive(s, e)}
                    className="opacity-70 hover:opacity-100 text-gray-400 hover:text-brand-600 transition-all cursor-pointer flex-shrink-0"
                    title="取消归档"
                  >
                    <ArchiveRestore className="w-3.5 h-3.5" />
                  </span>
                ) : (
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => toggleArchive(s, e)}
                    onKeyDown={(e) => e.key === 'Enter' && toggleArchive(s, e)}
                    className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-slate-500 transition-all cursor-pointer flex-shrink-0"
                    title="归档"
                  >
                    <Archive className="w-3.5 h-3.5" />
                  </span>
                )}
                <Trash2
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  className="w-3.5 h-3.5 text-gray-300 group-hover:text-red-400 flex-shrink-0 transition-colors"
                />
              </div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {s.message_count} 条消息 · {s.started_at ? formatDateTime(s.started_at) : ''}
                </div>
              </button>
              )
            ))
          )}
        </div>

        <div className="p-3 border-t" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-600 to-indigo-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0 shadow-sm">
                {user?.username?.[0]?.toUpperCase() || '?'}
              </div>
              <span className="text-sm font-medium text-gray-700 truncate">
                {user?.display_name || user?.username}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="退出登录"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 主区域 */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        <header
          className="sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b flex-shrink-0 backdrop-blur-xl"
          style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface-translucent)' }}
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-indigo-600 flex items-center justify-center shadow-md">
                <Brain className="w-5 h-5 text-white" />
              </div>
            <div>
              <h1 className="text-base font-bold text-gray-900">EduAgent</h1>
              <p className="text-xs text-gray-400">AI 编程学习伙伴</p>
            </div>
          </div>
          </div>
          <div className="flex items-center gap-1">
            {activeSessionId && messages.length > 0 && (
              <button
                onClick={exportMarkdown}
                className="p-2.5 rounded-lg text-gray-500 hover:text-brand-600 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                title="导出为 Markdown"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
            <ThemeToggle />
          </div>
        </header>

        {/* 消息区域 */}
        <div
          ref={scrollRef}
          onScroll={handleThreadScroll}
          className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
        >
          {showQuickQuestions ? (
            <div className="h-full flex flex-col items-center justify-center px-4">
              <div className="relative mb-5">
                <div className="absolute inset-0 bg-brand-500/20 blur-xl rounded-2xl" aria-hidden />
                <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg">
                  <Brain className="w-8 h-8 text-white" />
                </div>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                你好，{user?.display_name || user?.username}！
              </h2>
              <p className="text-sm text-gray-400 mb-7">告诉我你想学什么，我来帮你</p>
              <div className="flex flex-wrap gap-2.5 justify-center max-w-md">
                {QUICK_QUESTIONS.map((q, i) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className={cn('chip animate-fade-in', `animate-delay-${Math.min(i + 1, 3)}`)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              msg.content || msg.role === 'user' || editingMsgIdx === i ? (
                <MessageBubble
                  key={i}
                  index={i}
                  message={msg}
                  isLastAssistant={
                    i === messages.length - 1 ||
                    messages.slice(i + 1).every((m) => m.role !== 'assistant')
                      ? msg.role === 'assistant'
                      : false
                  }
                  sending={sending}
                  hasSession={!!activeSessionId}
                  isEditing={editingMsgIdx === i}
                  editDraft={editDraft}
                  onEditChange={setEditDraft}
                  onEditSave={commitEditMessage}
                  onEditCancel={() => setEditingMsgIdx(null)}
                  onStartEdit={() => startEditMessage(i)}
                  onRegenerate={!sending && !!activeSessionId ? handleRegenerate : undefined}
                  onRetry={msg.error ? () => sendMessage(msg.content, msg.timestamp - 1) : undefined}
                />
              ) : null
            ))
          )}

          {sending && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.content && (
            <div className="flex items-start gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-indigo-600 shadow-sm flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <div className="glass-card px-4 py-3.5 flex items-center gap-1.5">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
        </div>

        {/* 滚动到底部 */}
        {showScrollBtn && (
          <button
            onClick={() => scrollToBottom()}
            className="absolute bottom-28 left-1/2 -translate-x-1/2 z-20 p-2.5 rounded-full shadow-lg border transition-all hover:scale-105"
            style={{
              backgroundColor: 'var(--surface)',
              borderColor: 'var(--border-strong)',
              color: 'var(--text-muted)',
            }}
            title="滚动到底部"
          >
            <ArrowDown className="w-4 h-4" />
          </button>
        )}

        {/* 输入区域 */}
        <div className="flex-shrink-0 px-4 pt-3 pb-4" style={{ borderTop: '1px solid var(--border)', backgroundColor: 'var(--surface)' }}>
          <div className="flex items-end gap-2 max-w-4xl mx-auto glass-card !rounded-2xl p-2 shadow-md">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息，或问一个编程问题..."
              rows={1}
              className="input-field resize-none max-h-32 leading-relaxed !border-transparent !bg-transparent focus:!ring-0 dark:!bg-transparent"
              style={{ minHeight: '44px' }}
              disabled={sending}
            />
            {sending ? (
              <button
                onClick={handleStop}
                className="btn-secondary !p-0 w-11 h-11 flex-shrink-0 !rounded-xl"
                title="停止生成"
              >
                <Square className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => sendMessage(input)}
                disabled={!input.trim()}
                className="btn-primary !p-0 w-11 h-11 flex-shrink-0 !rounded-xl disabled:opacity-40"
                title="发送"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
          <p className="text-xs text-gray-300 mt-1.5 text-center">
            按 Enter 发送，Shift + Enter 换行
          </p>
        </div>
      </main>
    </div>
  )
}

/* ─────────────────── 消息气泡 ─────────────────── */

function MessageBubble({
  message,
  index,
  isLastAssistant,
  sending,
  hasSession,
  isEditing,
  editDraft,
  onEditChange,
  onEditSave,
  onEditCancel,
  onStartEdit,
  onRegenerate,
  onRetry,
}: {
  message: ChatMsg
  index: number
  isLastAssistant: boolean
  sending: boolean
  hasSession: boolean
  isEditing: boolean
  editDraft: string
  onEditChange: (v: string) => void
  onEditSave: () => void
  onEditCancel: () => void
  onStartEdit: () => void
  onRegenerate?: () => void
  onRetry?: () => void
}) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const canEdit = isUser && !!message.id && hasSession && !sending

  return (
    <div className={cn('flex items-start gap-2.5', isUser && 'flex-row-reverse')}>
      {isUser ? (
        <div className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0 text-sm font-bold text-gray-500 dark:text-gray-400">
          你
        </div>
      ) : (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-indigo-600 shadow-sm flex items-center justify-center flex-shrink-0">
          <Brain className="w-4 h-4 text-white" />
        </div>
      )}
      <div
        className={cn(
          'px-4 py-3 rounded-2xl max-w-[85%] sm:max-w-[75%] animate-fade-in group',
          isUser
            ? 'bg-gradient-to-br from-brand-600 to-indigo-600 text-white rounded-tr-md shadow-sm'
            : message.error
            ? 'glass-card text-red-600 rounded-tl-sm'
            : 'glass-card text-gray-700 rounded-tl-sm',
        )}
        title={new Date(message.timestamp).toLocaleString('zh-CN')}
      >
        {isEditing && isUser ? (
          <div className="min-w-[240px]">
            <textarea
              autoFocus
              value={editDraft}
              onChange={(e) => onEditChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') onEditCancel()
              }}
              rows={Math.min(6, Math.max(2, editDraft.split('\n').length))}
              className="w-full text-sm leading-relaxed whitespace-pre-wrap rounded-xl bg-white/95 text-gray-900 p-3 border border-white/40 focus:outline-none focus:ring-2 focus:ring-white/60 resize-none"
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                onClick={onEditCancel}
                className="px-3 py-1.5 text-xs rounded-lg bg-white/15 hover:bg-white/25 transition-colors"
              >
                取消
              </button>
              <button
                onClick={onEditSave}
                disabled={!editDraft.trim()}
                className="px-3 py-1.5 text-xs rounded-lg bg-white text-brand-700 font-medium hover:bg-brand-50 transition-colors disabled:opacity-40"
              >
                保存并重发
              </button>
            </div>
          </div>
        ) : isUser ? (
          <>
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
            <div className="mt-1.5 flex items-center gap-3 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
              {canEdit && (
                <button
                  onClick={onStartEdit}
                  className="flex items-center gap-1 text-[11px] text-white/60 hover:text-white transition-colors"
                  title="编辑并重发"
                >
                  <Pencil className="w-3 h-3" /> 编辑
                </button>
              )}
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[11px] text-white/60 hover:text-white transition-colors"
                title="复制"
              >
                {copied ? (
                  <><Check className="w-3 h-3" /> 已复制</>
                ) : (
                  <><Copy className="w-3 h-3" /> 复制</>
                )}
              </button>
            </div>
          </>
        ) : message.error ? (
          <div className="flex items-center gap-2">
            <p className="text-sm leading-relaxed">{message.content}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="p-1 text-gray-400 hover:text-brand-600 transition-colors"
                title="重试"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ) : (
          <div className="text-sm leading-relaxed break-words">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                pre({ children }) {
                  return <>{children}</>
                },
                code({ className, children, ...props }) {
                  const isInline = !className && !String(children).includes('\n')
                  if (isInline) {
                    return (
                      <code className="bg-gray-100 dark:bg-slate-800 text-pink-600 dark:text-pink-400 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                        {children}
                      </code>
                    )
                  }
                  const codeText = String(children).replace(/\n$/, '')
                  const lang =
                    /language-([\w+-]+)/.exec(className || '')?.[1] || '代码'
                  return (
                    <div className="my-2 rounded-lg overflow-hidden border border-gray-700/60">
                      <div className="flex items-center justify-between bg-gray-800 px-3 py-1.5">
                        <span className="text-[11px] font-mono text-gray-400">{lang}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(codeText)}
                          className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white transition-colors"
                          title="复制代码"
                        >
                          <Copy className="w-3 h-3" /> 复制
                        </button>
                      </div>
                      <pre className="bg-gray-900 text-green-400 p-3 text-xs font-mono overflow-x-auto">
                        <code>{children}</code>
                      </pre>
                    </div>
                  )
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* 助手消息操作行：复制 + 重新生成（仅最后一轮） */}
        {!isUser && !message.error && message.content && (
          <div className="mt-1 flex items-center gap-4 text-xs text-gray-400">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              {copied ? (
                <><Check className="w-3 h-3" /> 已复制</>
              ) : (
                <><Copy className="w-3 h-3" /> 复制</>
              )}
            </button>
            {onRegenerate && isLastAssistant && (
              <button
                onClick={onRegenerate}
                disabled={sending}
                className="flex items-center gap-1 hover:text-brand-600 dark:hover:text-brand-300 transition-colors disabled:opacity-40"
                title="重新生成回复"
              >
                {sending ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RefreshCw className="w-3 h-3" />
                )}
                重新生成
              </button>
            )}
          </div>
        )}

        {/* 代码执行结果卡片 */}
        {message.codeResult && (
          <CodeResultCard result={message.codeResult} />
        )}
        {/* 题目卡片 */}
        {message.quiz && (
          <QuizCard quiz={message.quiz} judged={message.judged} />
        )}
      </div>
    </div>
  )
}

/* ─────────────────── 代码执行结果卡片 ─────────────────── */

function CodeResultCard({ result }: { result: CodeResult }) {
  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="text-xs font-medium text-gray-600 mb-2 flex items-center gap-1">
        <Terminal className="w-3 h-3" /> 代码执行结果
        <span className={cn('ml-1', result.success ? 'text-green-600' : 'text-red-600')}>
          {result.success ? '✓ 成功' : '✗ 失败'}
        </span>
      </div>
      {result.stdout && (
        <div className="relative group bg-gray-900 text-green-400 p-3 rounded-lg text-xs font-mono overflow-x-auto mb-2">
          <pre className="whitespace-pre-wrap">{result.stdout}</pre>
          <button
            onClick={() => navigator.clipboard.writeText(result.stdout)}
            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white transition-all text-xs px-2 py-1 bg-gray-800 rounded"
          >
            复制
          </button>
        </div>
      )}
      {result.stderr && (
        <div className="relative group bg-gray-900 text-red-400 p-3 rounded-lg text-xs font-mono overflow-x-auto">
          <pre className="whitespace-pre-wrap">{result.stderr}</pre>
          <button
            onClick={() => navigator.clipboard.writeText(result.stderr)}
            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white transition-all text-xs px-2 py-1 bg-gray-800 rounded"
          >
            复制
          </button>
        </div>
      )}
      {!result.stdout && !result.stderr && (
        <div className="text-xs text-gray-400 italic">(无输出)</div>
      )}
    </div>
  )
}

/* ─────────────────── 题目卡片 ─────────────────── */

function QuizCard({ quiz, judged }: { quiz: QuizData; judged?: JudgedSummary }) {
  // 已作答的题（历史回看或判题完成）：直接展示对错高亮，不可再点
  const alreadyAnswered = Boolean(quiz.answered) || Boolean(judged)
  const [selected, setSelected] = useState<number | null>(
    alreadyAnswered ? (judged?.selected ?? null) : null,
  )
  const [showResult, setShowResult] = useState(alreadyAnswered)

  const handleSelect = (idx: number) => {
    if (showResult) return
    setSelected(idx)
    setShowResult(true)
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="text-xs font-medium text-brand-600 mb-2 flex items-center gap-1">
        <Sparkles className="w-3 h-3" /> 选择题
        {quiz.difficulty && (
          <span className="text-gray-400 ml-1">· {quiz.difficulty}</span>
        )}
      </div>
      <p className="text-sm font-medium text-gray-800 mb-3">{quiz.question}</p>
      <div className="space-y-2">
        {quiz.options.map((opt, idx) => {
          let cls = 'bg-gray-50 hover:bg-gray-100 border-gray-200'
          if (showResult && idx === quiz.answer) {
            cls = 'bg-green-50 border-green-500'
          } else if (showResult && idx === selected && idx !== quiz.answer) {
            cls = 'bg-red-50 border-red-500'
          }
          return (
            <button
              key={idx}
              onClick={() => handleSelect(idx)}
              disabled={showResult}
              className={cn(
                'w-full text-left px-3 py-2 rounded-lg border text-sm transition-colors',
                cls,
                !showResult && 'cursor-pointer',
              )}
            >
              <span className="text-gray-400 mr-2">{String.fromCharCode(65 + idx)}.</span>
              {opt}
            </button>
          )
        })}
      </div>
      {showResult && quiz.explanation && (
        <div className="mt-3 p-3 bg-brand-50 rounded-lg text-sm text-gray-700">
          <span className="font-semibold">解析：</span>
          {quiz.explanation}
        </div>
      )}
    </div>
  )
}

/* ─────────────────── 快捷问题 ─────────────────── */

const QUICK_QUESTIONS = [
  '什么是 Python 递归？',
  '给我出几道 Python 基础题',
  '列表和元组有什么区别？',
  '帮我运行：print(sum(range(1, 101)))',
]
