'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Users, Send, Sparkles, Trash2, Loader2,
  ChevronLeft, User as UserIcon, AlertCircle, Heart,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { aiAPI } from '@/lib/api'
import { BUDDY_QUICK_QUESTIONS } from '@/lib/constants'
import { cn } from '@/lib/utils'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

const STORAGE_KEY = 'eduflow_chat_buddy'

export default function AiBuddyPage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  // 加载本地聊天记录
  useEffect(() => {
    if (!user) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const saved = JSON.parse(raw) as ChatMessage[]
        if (Array.isArray(saved) && saved.length > 0) {
          setMessages(saved)
          return
        }
      }
    } catch {
      /* ignore */
    }
    // 初始欢迎消息
    setMessages([
      {
        role: 'assistant',
        content: `嘿${user.display_name ? '，' + user.display_name : ''}！我是你的 AI 伴学 🤝\n\n咱们可以一起复习知识点、做做小测验、聊聊天。学习路上有个伙伴不孤单，一起加油吧！`,
        timestamp: Date.now(),
      },
    ])
  }, [user])

  // 保存聊天记录到 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-50)))
      } catch {
        /* ignore */
      }
    }
  }, [messages])

  // 自动滚动到底部
  useEffect(() => {
    const el = scrollRef.current
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    }
  }, [messages, sending])

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return

    setError('')
    const userMsg: ChatMessage = {
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setSending(true)

    try {
      const res = await aiAPI.chat(trimmed, 'buddy', {
        user_id: user?.id,
        username: user?.username,
      })
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: res.response || res.toString() || '（伴学暂时没有回复，请稍后再试）',
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : '发送失败'
      setError(errMsg)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `哎呀，出了点小状况：${errMsg}\n\n可能是后端 AI 服务还没启动，等一下再试试吧～`,
          timestamp: Date.now(),
        },
      ])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }, [sending, user])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleClear = () => {
    setMessages([
      {
        role: 'assistant',
        content: '对话已清空，我们重新开始吧！有什么想聊的？',
        timestamp: Date.now(),
      },
    ])
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      /* ignore */
    }
  }

  if (loading) return <FullScreenLoader />
  if (!user) return null

  const showQuickQuestions = messages.filter(m => m.role === 'user').length === 0

  return (
    <main className="max-w-4xl mx-auto px-4 py-6 pb-4 h-[calc(100vh-4rem)] flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="lg:hidden w-9 h-9 rounded-full flex items-center justify-center text-gray-500 hover:bg-gray-100"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center shadow-md">
            <Users className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">AI 伴学</h1>
            <p className="text-xs text-gray-400">协同练习 · 像同学一样讨论</p>
          </div>
        </div>
        <button
          onClick={handleClear}
          className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
          title="清空对话"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* 消息区域 */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 pb-4"
      >
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {/* 发送中加载 */}
        {sending && (
          <div className="flex items-start gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center flex-shrink-0">
              <Users className="w-4 h-4 text-white" />
            </div>
            <div className="glass-card px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-teal-500 animate-spin" />
              <span className="text-sm text-gray-400">伴学正在打字...</span>
            </div>
          </div>
        )}

        {/* 快捷问题 */}
        {showQuickQuestions && !sending && (
          <div className="pt-2">
            <div className="flex items-center gap-1.5 text-sm text-gray-400 mb-3">
              <Sparkles className="w-4 h-4" /> 来聊点什么吧
            </div>
            <div className="flex flex-wrap gap-2">
              {BUDDY_QUICK_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q)}
                  className="px-4 py-2 rounded-full text-sm bg-white border border-teal-200 text-teal-600 hover:bg-teal-50 hover:border-teal-300 transition-all duration-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="flex-shrink-0 pt-3 border-t border-gray-100">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="和 AI 伴学聊点什么..."
              rows={1}
              className="input-field resize-none pr-12 max-h-32 leading-relaxed"
              style={{ minHeight: '48px' }}
              disabled={sending}
            />
          </div>
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || sending}
            className="inline-flex items-center justify-center gap-2 bg-teal-500 text-white px-4 py-3 rounded-full font-medium hover:bg-teal-600 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-300 mt-1.5 text-center">
          按 Enter 发送，Shift + Enter 换行
        </p>
      </div>
    </main>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex items-start gap-2.5', isUser && 'flex-row-reverse')}>
      {/* 头像 */}
      {isUser ? (
        <div className="w-8 h-8 rounded-lg bg-gray-200 flex items-center justify-center flex-shrink-0">
          <UserIcon className="w-4 h-4 text-gray-500" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center flex-shrink-0">
          <Heart className="w-4 h-4 text-white" />
        </div>
      )}

      {/* 消息内容 */}
      <div
        className={cn(
          'px-4 py-3 rounded-2xl max-w-[75%]',
          isUser
            ? 'bg-teal-500 text-white rounded-tr-sm'
            : 'glass-card text-gray-700 rounded-tl-sm'
        )}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
      </div>
    </div>
  )
}

function FullScreenLoader() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-gray-400">
        <div className="w-8 h-8 border-2 border-teal-200 border-t-teal-500 rounded-full animate-spin" />
        <span className="text-sm">加载中...</span>
      </div>
    </div>
  )
}
