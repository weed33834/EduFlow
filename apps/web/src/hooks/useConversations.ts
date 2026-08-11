'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { conversationAPI, type Conversation } from '@/lib/api'

export interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

/**
 * 服务端会话持久化 Hook：管理会话列表、当前会话与消息。
 * 服务端不可用时自动降级为仅本地(localStorage)，不阻塞对话。
 */
export function useConversations(agentType: 'tutor' | 'buddy', storageKey: string) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [serverReady, setServerReady] = useState(true)
  const storageKeyRef = useRef(storageKey)

  // 本地存储读写
  const persistLocal = useCallback((msgs: ChatMsg[]) => {
    try {
      localStorage.setItem(storageKeyRef.current, JSON.stringify(msgs.slice(-50)))
    } catch { /* ignore */ }
  }, [])

  const loadLocal = useCallback((): ChatMsg[] => {
    try {
      const raw = localStorage.getItem(storageKeyRef.current)
      if (raw) {
        const saved = JSON.parse(raw) as ChatMsg[]
        if (Array.isArray(saved)) return saved
      }
    } catch { /* ignore */ }
    return []
  }, [])

  // 刷新会话列表（服务端）
  const refresh = useCallback(async () => {
    try {
      const data = await conversationAPI.list()
      setConversations(data.conversations)
      setServerReady(true)
    } catch {
      setServerReady(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // 加载本地历史作为初始回退
  useEffect(() => {
    if (messages.length === 0) {
      const local = loadLocal()
      if (local.length > 0) setMessages(local)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 切换会话
  const select = useCallback(async (id: number) => {
    setActiveId(id)
    try {
      const detail = await conversationAPI.get(id)
      setMessages(detail.messages.map(m => ({ role: m.role, content: m.content, timestamp: Date.now() })))
    } catch {
      setMessages(loadLocal())
    }
  }, [loadLocal])

  // 新建会话
  const newConversation = useCallback(async () => {
    setActiveId(null)
    setMessages([])
    if (serverReady) {
      try {
        const conv = await conversationAPI.create(agentType)
        setConversations(prev => [conv, ...prev])
        setActiveId(conv.id)
      } catch { /* keep local-only */ }
    }
  }, [serverReady, agentType])

  // 追加消息（本地立即生效 + 服务端持久化）
  const append = useCallback(async (role: 'user' | 'assistant', content: string) => {
    const next = [...messagesRef(), { role, content, timestamp: Date.now() }]
    setMessages(next)
    persistLocal(next)
    if (activeId) {
      try {
        await conversationAPI.appendMessage(activeId, role, content)
        refresh()
      } catch { /* ignore */ }
    }
  }, [activeId, persistLocal, refresh])

  function messagesRef(): ChatMsg[] {
    // 读取最新消息：通过闭包取不到时回退到 state（append 依赖 activeId 稳定即可）
    return messages
  }

  return {
    conversations,
    activeId,
    messages,
    setMessages,
    serverReady,
    refresh,
    select,
    newConversation,
    append,
  }
}
