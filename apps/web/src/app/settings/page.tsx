'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  User, Save, Camera, FileText, ChevronLeft, CheckCircle,
  AlertCircle, Loader2,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { authAPI } from '@/lib/api'
import { getInitials } from '@/lib/utils'

export default function SettingsPage() {
  const router = useRouter()
  const { user, loading, updateUser } = useAuth()

  const [displayName, setDisplayName] = useState('')
  const [bio, setBio] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')

  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  // 初始化表单数据
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '')
      setBio(user.bio || '')
      setAvatarUrl(user.avatar_url || '')
    }
  }, [user])

  if (loading) return <FullScreenLoader />
  if (!user) return null

  const handleSave = async () => {
    setError('')
    setSuccess(false)

    const trimmedName = displayName.trim()
    if (!trimmedName) {
      setError('昵称不能为空')
      return
    }

    setSaving(true)
    try {
      const updated = await authAPI.updateMe({
        display_name: trimmedName,
        bio: bio.trim(),
        avatar_url: avatarUrl.trim() || undefined,
      })
      updateUser(updated)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-8 pb-24">
      {/* 头部 */}
      <div className="mb-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-brand-600 transition-colors mb-4"
        >
          <ChevronLeft className="w-4 h-4" /> 返回仪表盘
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <User className="w-6 h-6 text-brand-600" /> 个人设置
        </h1>
        <p className="text-gray-500 mt-1 text-sm">管理你的个人信息和偏好</p>
      </div>

      {/* 头像预览 */}
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center gap-5">
          <AvatarPreview avatarUrl={avatarUrl} displayName={displayName} username={user.username} />
          <div className="flex-1">
            <label className="label flex items-center gap-1.5">
              <Camera className="w-4 h-4 text-gray-400" /> 头像 URL
            </label>
            <input
              type="url"
              className="input-field"
              placeholder="https://example.com/avatar.png"
              value={avatarUrl}
              onChange={e => setAvatarUrl(e.target.value)}
            />
            <p className="text-xs text-gray-400 mt-1.5">粘贴图片链接即可更新头像，留空使用默认头像</p>
          </div>
        </div>
      </div>

      {/* 表单 */}
      <div className="glass-card p-6 space-y-5">
        {/* 昵称 */}
        <div>
          <label className="label" htmlFor="displayName">
            昵称
          </label>
          <input
            id="displayName"
            type="text"
            className="input-field"
            placeholder="请输入昵称"
            maxLength={30}
            value={displayName}
            onChange={e => {
              setDisplayName(e.target.value)
              setSuccess(false)
            }}
          />
          <div className="flex justify-between mt-1.5">
            <p className="text-xs text-gray-400">将显示在导航栏和个人资料中</p>
            <span className="text-xs text-gray-300">{displayName.length}/30</span>
          </div>
        </div>

        {/* 邮箱（只读） */}
        <div>
          <label className="label">邮箱</label>
          <input
            type="email"
            className="input-field bg-gray-50 text-gray-400 cursor-not-allowed"
            value={user.email}
            disabled
          />
          <p className="text-xs text-gray-400 mt-1.5">邮箱不可修改</p>
        </div>

        {/* 用户名（只读） */}
        <div>
          <label className="label">用户名</label>
          <input
            type="text"
            className="input-field bg-gray-50 text-gray-400 cursor-not-allowed"
            value={user.username}
            disabled
          />
        </div>

        {/* 简介 */}
        <div>
          <label className="label flex items-center gap-1.5" htmlFor="bio">
            <FileText className="w-4 h-4 text-gray-400" /> 个人简介
          </label>
          <textarea
            id="bio"
            className="input-field min-h-[100px] resize-y"
            placeholder="介绍一下自己吧..."
            maxLength={200}
            value={bio}
            onChange={e => {
              setBio(e.target.value)
              setSuccess(false)
            }}
          />
          <div className="flex justify-between mt-1.5">
            <p className="text-xs text-gray-400">让 AI 更好地了解你，提供个性化建议</p>
            <span className="text-xs text-gray-300">{bio.length}/200</span>
          </div>
        </div>

        {/* 提示信息 */}
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-green-50 border border-green-100 text-sm text-green-600">
            <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>保存成功！个人信息已更新</span>
          </div>
        )}

        {/* 保存按钮 */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              setDisplayName(user.display_name || '')
              setBio(user.bio || '')
              setAvatarUrl(user.avatar_url || '')
              setSuccess(false)
              setError('')
            }}
            disabled={saving}
          >
            重置
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> 保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> 保存修改
              </>
            )}
          </button>
        </div>
      </div>

      {/* 账户信息 */}
      <div className="glass-card p-6 mt-6">
        <h2 className="text-sm font-bold text-gray-700 mb-4">账户信息</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">账户ID</span>
            <span className="text-gray-600 font-mono">{user.id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">注册时间</span>
            <span className="text-gray-600">
              {user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '-'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">账户状态</span>
            <span className="inline-flex items-center gap-1 text-green-600">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" /> 活跃
            </span>
          </div>
        </div>
      </div>
    </main>
  )
}

function AvatarPreview({
  avatarUrl,
  displayName,
  username,
}: {
  avatarUrl: string
  displayName: string
  username: string
}) {
  const [imgError, setImgError] = useState(false)

  if (avatarUrl && !imgError) {
    return (
      <img
        src={avatarUrl}
        alt="头像预览"
        className="w-20 h-20 rounded-full object-cover border-2 border-white shadow-md"
        onError={() => setImgError(true)}
      />
    )
  }

  const initials = getInitials(displayName || username)
  return (
    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold border-2 border-white shadow-md">
      {initials}
    </div>
  )
}

function FullScreenLoader() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-gray-400">
        <div className="w-8 h-8 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
        <span className="text-sm">加载中...</span>
      </div>
    </div>
  )
}
