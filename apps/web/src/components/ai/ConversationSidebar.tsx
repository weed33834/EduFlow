'use client'

import { Plus, Trash2, MessageSquare, RefreshCw, WifiOff } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { conversationAPI, type Conversation } from '@/lib/api'
import { cn } from '@/lib/utils'

interface Props {
  conversations: Conversation[]
  activeId: number | null
  serverReady: boolean
  onSelect: (id: number) => void
  onNew: () => void
  onChanged: () => void
}

export default function ConversationSidebar({
  conversations,
  activeId,
  serverReady,
  onSelect,
  onNew,
  onChanged,
}: Props) {
  const router = useRouter()

  const remove = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await conversationAPI.remove(id)
      if (activeId === id) {
        router.refresh()
        onNew()
      }
      onChanged()
    } catch { /* ignore */ }
  }

  return (
    <aside className="w-full lg:w-64 flex-shrink-0 flex flex-col border-r border-gray-100 bg-white/60 lg:min-h-[calc(100vh-4rem)]">
      <div className="p-3 space-y-2">
        <button
          onClick={onNew}
          className="w-full flex items-center gap-2 justify-center btn-primary !py-2.5 text-sm"
        >
          <Plus className="w-4 h-4" /> 新对话
        </button>
        {!serverReady && (
          <div className="flex items-center gap-1.5 text-xs text-amber-600 px-1">
            <WifiOff className="w-3.5 h-3.5" /> 离线模式（仅本地保存）
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
        {conversations.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-6 px-2">
            还没有会话，点击上方「新对话」开始
          </p>
        ) : (
          conversations.map(c => (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-left text-sm transition-colors group',
                activeId === c.id ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-50'
              )}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0 opacity-60" />
              <span className="flex-1 min-w-0">
                <span className="block truncate font-medium">{c.title}</span>
                {c.last_message && (
                  <span className="block truncate text-xs text-gray-400">{c.last_message}</span>
                )}
              </span>
              <span
                role="button"
                tabIndex={-1}
                onClick={e => remove(c.id, e)}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
                aria-label="删除会话"
              >
                <Trash2 className="w-4 h-4" />
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  )
}
