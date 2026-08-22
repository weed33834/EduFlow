'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Send, Sparkles, Loader2, Plus, Trash2, MessageSquare,
  LogOut, Menu, X, Brain, Terminal,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  chatStream, sessionAPI,
  type ChatResponseData, type SessionSummary, type CodeResult, type QuizData,
} from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn, formatDateTime } from '@/lib/utils'

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  quiz?: QuizData
  codeResult?: CodeResult
  timestamp: number
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

  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 加载会话列表
  const loadSessions = useCallback(async () => {
    try {
      const list = await sessionAPI.list()
      setSessions(list)
    } catch {
      setSessions([])
    } finally {
      setLoadingSessions(false)
    }
  }, [])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // 自动滚动
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const handleSelectSession = useCallback(async (id: number) => {
    setActiveSessionId(id)
    setSidebarOpen(false)
    try {
      const detail = await sessionAPI.get(id)
      setMessages(
        detail.messages.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
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

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || sending) return

      setInput('')
      setSending(true)

      // 乐观添加用户消息
      const userTs = Date.now()
      const userMsg: ChatMsg = {
        role: 'user',
        content: trimmed,
        timestamp: userTs,
      }

      // 助手占位消息
      const assistantTs = userTs + 1
      const assistantMsg: ChatMsg = {
        role: 'assistant',
        content: '',
        timestamp: assistantTs,
      }
      setMessages((prev) => [...prev, userMsg, assistantMsg])

      await chatStream(
        trimmed,
        activeSessionId,
        (data: ChatResponseData) => {
          if (data.type === 'status') {
            // 状态提示 — 不更新消息内容，thinking 指示器会自动显示
            return
          }
          if (data.type === 'stream') {
            // 流式文本 — 追加到消息内容
            setMessages((prev) =>
              prev.map((m) =>
                m.timestamp === assistantTs
                  ? { ...m, content: m.content + data.content }
                  : m,
              ),
            )
            return
          }
          // type === 'complete' — 设置最终内容 + 元数据
          setMessages((prev) =>
            prev.map((m) =>
              m.timestamp === assistantTs
                ? {
                    role: 'assistant',
                    content: data.content,
                    quiz: data.quiz,
                    codeResult: data.code_result,
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
                    content: `出错了：${err.message}`,
                    timestamp: assistantTs,
                  }
                : m,
            ),
          )
        },
      )

      // 刷新会话列表
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

  const handleLogout = () => {
    logout()
    router.push('/')
  }

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

        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="btn-primary w-full !py-2 text-sm"
          >
            <Plus className="w-4 h-4" /> 新对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-1">
          {loadingSessions ? (
            <div className="text-center py-4 text-sm text-gray-400">加载中...</div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-400">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
              还没有对话
            </div>
          ) : (
            sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                className={cn(
                  'w-full text-left px-3 py-2.5 rounded-lg transition-colors group',
                  activeSessionId === s.id
                    ? 'bg-brand-50 text-brand-700'
                    : 'hover:bg-gray-50 text-gray-600',
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium truncate flex-1">
                    {s.last_message || `对话 #${s.id}`}
                  </span>
                  <Trash2
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="w-3.5 h-3.5 text-gray-300 group-hover:text-red-400 flex-shrink-0"
                  />
                </div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {s.message_count} 条消息 · {s.started_at ? formatDateTime(s.started_at) : ''}
                </div>
              </button>
            ))
          )}
        </div>

        <div className="p-3 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
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
      <main className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center shadow-sm">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold text-gray-900">EduAgent</h1>
                <p className="text-xs text-gray-400">AI 编程学习伙伴</p>
              </div>
            </div>
          </div>
        </header>

        {/* 消息区域 */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {showQuickQuestions ? (
            <div className="h-full flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-brand-600" />
              </div>
              <h2 className="text-lg font-bold text-gray-700 mb-2">
                你好，{user?.display_name || user?.username}！
              </h2>
              <p className="text-sm text-gray-400 mb-6">告诉我你想学什么，我来帮你</p>
              <div className="flex flex-wrap gap-2 justify-center max-w-md">
                {QUICK_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="px-4 py-2 rounded-full text-sm bg-white border border-brand-200 text-brand-600 hover:bg-brand-50 hover:border-brand-300 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              msg.content || msg.role === 'user' ? (
                <MessageBubble key={i} message={msg} />
              ) : null
            ))
          )}

          {sending && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.content && (
            <div className="flex items-start gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <div className="glass-card px-4 py-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />
                <span className="text-sm text-gray-400">Agent 正在思考...</span>
              </div>
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="flex-shrink-0 px-4 pt-3 pb-4 border-t border-gray-100">
          <div className="flex items-end gap-2 max-w-4xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息，或问一个编程问题..."
              rows={1}
              className="input-field resize-none max-h-32 leading-relaxed"
              style={{ minHeight: '48px' }}
              disabled={sending}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || sending}
              className="btn-primary !px-4 !py-3 flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
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

function MessageBubble({ message }: { message: ChatMsg }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex items-start gap-2.5', isUser && 'flex-row-reverse')}>
      {isUser ? (
        <div className="w-8 h-8 rounded-lg bg-gray-200 flex items-center justify-center flex-shrink-0 text-sm font-bold text-gray-500">
          你
        </div>
      ) : (
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center flex-shrink-0">
          <Brain className="w-4 h-4 text-white" />
        </div>
      )}
      <div
        className={cn(
          'px-4 py-3 rounded-2xl max-w-[75%] animate-fade-in',
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'glass-card text-gray-700 rounded-tl-sm',
        )}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
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
                    <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                      {children}
                    </code>
                  )
                }
                const codeText = String(children).replace(/\n$/, '')
                return (
                  <div className="relative group my-2">
                    <pre className="bg-gray-900 text-green-400 p-3 rounded-lg text-xs font-mono overflow-x-auto">
                      <code className={className}>{children}</code>
                    </pre>
                    <button
                      onClick={() => navigator.clipboard.writeText(codeText)}
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white transition-all text-xs px-2 py-1 bg-gray-800 rounded"
                    >
                      复制
                    </button>
                  </div>
                )
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
          </div>
        )}
        {/* 代码执行结果卡片 */}
        {message.codeResult && (
          <CodeResultCard result={message.codeResult} />
        )}
        {/* 题目卡片 */}
        {message.quiz && (
          <QuizCard quiz={message.quiz} />
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

function QuizCard({ quiz }: { quiz: QuizData }) {
  const [selected, setSelected] = useState<number | null>(null)
  const [showResult, setShowResult] = useState(false)

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
