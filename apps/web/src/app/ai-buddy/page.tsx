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
import { useConversations, type ChatMsg } from '@/hooks/useConversations'
import ConversationSidebar from '@/components/ai/ConversationSidebar'

const STORAGE_KEY = 'eduflow_chat_buddy'

export default function AiBuddyPage() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const { conversations, activeId, messages, setMessages, serverReady, refresh, select, newConversation, append } =
    useConversations('buddy', STORAGE_KEY)

  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return
    setError('')
    setInput('')
    setSending(true)

    await append('user', trimmed)
    const history = [
      ...messages.map(m => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content: trimmed },
    ]

    try {
      const assistantId = Date.now() + 1
      setMessages(prev => [...prev, { role: 'assistant', content: '', timestamp: assistantId }])
      let acc = ''
      await aiAPI.chatStream(
        trimmed,
        'buddy',
        { user_id: user?.id, username: user?.username },
        history,
        delta => {
          acc += delta
          setMessages(prev => prev.map(m => (m.timestamp === assistantId ? { ...m, content: acc } : m)))
        }
      )
      await append('assistant', acc || '（伴学暂时没有回复，请稍后再试）')
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : '发送失败'
      setError(errMsg)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `哎呀，出了点小状况：${errMsg}\n\n可能是后端 AI 服务还没启动，等一下再试试吧～`,
        timestamp: Date.now(),
      }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }, [sending, user, append, messages, setMessages])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  if (loading) return <FullScreenLoader />
  if (!user) return null

  const showQuickQuestions = messages.filter(m => m.role === 'user').length === 0

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-4rem)] flex">
      <ConversationSidebar
        conversations={conversations}
        activeId={activeId}
        serverReady={serverReady}
        onSelect={select}
        onNew={newConversation}
        onChanged={refresh}
      />
      <main className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="lg:hidden w-9 h-9 rounded-full flex items-center justify-center text-gray-500 hover:bg-gray-100">
              <ChevronLeft className="w-5 h-5" />
            </Link>
            <div className="w-11 h-11 rounded-xl bg-teal-500 flex items-center justify-center shadow-md">
              <Users className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">AI 伴学</h1>
              <p className="text-xs text-gray-400">协同练习 · 像同学一样讨论 · 云端记忆</p>
            </div>
          </div>
          <button
            onClick={newConversation}
            className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
            title="新对话"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* 切换：AI导师 / AI伴学 */}
        <div className="px-4 pb-2 -mt-1 flex-shrink-0">
          <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5">
            <Link href="/ai-tutor" className="px-3 py-1.5 text-sm font-medium rounded-md text-gray-500 hover:text-gray-700">AI 导师</Link>
            <Link href="/ai-buddy" className="px-3 py-1.5 text-sm font-medium rounded-md bg-white text-teal-600 shadow-sm">AI 伴学</Link>
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 px-4 py-4">
          {messages.map((msg, i) => <MessageBubble key={i} message={msg} />)}

          {sending && (
            <div className="flex items-start gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center flex-shrink-0">
                <Users className="w-4 h-4 text-white" />
              </div>
              <div className="glass-card px-4 py-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-teal-500 animate-spin" />
                <span className="text-sm text-gray-400">伴学正在打字...</span>
              </div>
            </div>
          )}

          {showQuickQuestions && !sending && (
            <div className="pt-2">
              <div className="flex items-center gap-1.5 text-sm text-gray-400 mb-3">
                <Sparkles className="w-4 h-4" /> 来聊点什么吧
              </div>
              <div className="flex flex-wrap gap-2">
                {BUDDY_QUICK_QUESTIONS.map((q, i) => (
                  <button key={i} onClick={() => sendMessage(q)}
                    className="px-4 py-2 rounded-full text-sm bg-white border border-teal-200 text-teal-600 hover:bg-teal-50 hover:border-teal-300 transition-all duration-200">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className="flex-shrink-0 px-4 pt-3 pb-2 border-t border-gray-100">
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
            <button onClick={() => sendMessage(input)} disabled={!input.trim() || sending}
              className="inline-flex items-center justify-center gap-2 bg-teal-500 text-white px-4 py-3 rounded-full font-medium hover:bg-teal-600 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm flex-shrink-0">
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-gray-300 mt-1.5 text-center">按 Enter 发送，Shift + Enter 换行</p>
        </div>
      </main>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMsg }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex items-start gap-2.5', isUser && 'flex-row-reverse')}>
      {isUser ? (
        <div className="w-8 h-8 rounded-lg bg-gray-200 flex items-center justify-center flex-shrink-0">
          <UserIcon className="w-4 h-4 text-gray-500" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center flex-shrink-0">
          <Heart className="w-4 h-4 text-white" />
        </div>
      )}
      <div className={cn('px-4 py-3 rounded-2xl max-w-[75%]', isUser ? 'bg-teal-500 text-white rounded-tr-sm' : 'glass-card text-gray-700 rounded-tl-sm')}>
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
