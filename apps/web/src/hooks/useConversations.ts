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
 * - 首条消息自动创建服务端会话并持久化
 * - 服务端不可用时自动降级为仅本地(localStorage)
 */
export function useConversations(agentType: 'tutor' | 'buddy', storageKey: string) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [serverReady, setServerReady] = useState(true)
  const storageKeyRef = useRef(storageKey)
  const activeIdRef = useRef<number | null>(null)
  const messagesRef = useRef<ChatMsg[]>([])
  // 防止并发 append 时重复创建会话
  const creatingRef = useRef(false)

  useEffect(() => { activeIdRef.current = activeId }, [activeId])
  useEffect(() => { messagesRef.current = messages }, [messages])

  const persistLocal = useCallback((msgs: ChatMsg[]) => {
    try { localStorage.setItem(storageKeyRef.current, JSON.stringify(msgs.slice(-50))) } catch { /* ignore */ }
  }, [])

  // 刷新会话列表
  const refresh = useCallback(async () => {
    try {
      const data = await conversationAPI.list()
      setConversations(data.conversations)
      setServerReady(true)
    } catch { setServerReady(false) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // 从本地恢复历史（仅服务端不可用或无会话时）
  useEffect(() => {
    if (messagesRef.current.length === 0) {
      try {
        const raw = localStorage.getItem(storageKeyRef.current)
        if (raw) {
          const saved = JSON.parse(raw) as ChatMsg[]
          if (Array.isArray(saved) && saved.length) setMessages(saved)
        }
      } catch { /* ignore */ }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const select = useCallback(async (id: number) => {
    setActiveId(id)
    try {
      const detail = await conversationAPI.get(id)
      setMessages(detail.messages.map(m => ({ role: m.role, content: m.content, timestamp: Date.now() })))
    } catch { /* keep local */ }
  }, [])

  const newConversation = useCallback(async () => {
    setActiveId(null)
    setMessages([])
    if (serverReady) {
      try {
        const conv = await conversationAPI.create(agentType)
        setConversations(prev => [conv, ...prev])
        setActiveId(conv.id)
      } catch { /* local-only */ }
    }
  }, [serverReady, agentType])

  /**
   * 追加消息：本地即时生效 + 服务端持久化。
   * 若尚无会话且是用户消息，自动创建服务端会话。
   */
  const append = useCallback(async (role: 'user' | 'assistant', content: string) => {
    // 用函数式更新，避免过期闭包
    setMessages(prev => {
      const next = [...prev, { role, content, timestamp: Date.now() }]
      persistLocal(next)
      return next
    })

    let cid = activeIdRef.current
    // 无会话且首次发用户消息 -> 自动创建
    if (cid === null && role === 'user' && !creatingRef.current) {
      creatingRef.current = true
      try {
        const conv = await conversationAPI.create(agentType)
        cid = conv.id
        setActiveId(cid)
        setConversations(prev => [conv, ...prev.filter(c => c.id !== conv.id)])
        await conversationAPI.appendMessage(cid, role, content)
        await refresh()
        return
      } catch {
        // 服务端不可用：仅本地
      } finally {
        creatingRef.current = false
      }
    }
    if (cid !== null) {
      try {
        await conversationAPI.appendMessage(cid, role, content)
        refresh()
      } catch { /* ignore */ }
    }
  }, [agentType, persistLocal, refresh])

  /**
   * 仅服务端持久化，不修改本地消息状态。
   * 用于流式回复：助手内容已在本地占位，只需同步到服务端。
   */
  const persistOnly = useCallback(async (role: 'user' | 'assistant', content: string) => {
    const cid = activeIdRef.current
    if (cid === null) return
    try {
      await conversationAPI.appendMessage(cid, role, content)
      refresh()
    } catch { /* ignore */ }
  }, [refresh])

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
    persistOnly,
  }
}
