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

  // 模型能力探测
  const [caps, setCaps] = useState<import('@/lib/api').CapabilitiesInfo | null>(null)
  const [capsLoading, setCapsLoading] = useState(true)

  // 模型配置
  const [mc, setMc] = useState({
    base_url: '', api_key: '', llm_model: '', tts_model: '', asr_model: '', image_model: '', video_model: '', tts_voice: '',
  })
  const [mcLoaded, setMcLoaded] = useState(false)
  const [mcSaving, setMcSaving] = useState(false)
  const [mcMsg, setMcMsg] = useState('')
  const [mcTest, setMcTest] = useState('')

  useEffect(() => {
    Promise.all([
      import('@/lib/api').then(({ aiAPI }) => aiAPI.capabilities().catch(() => null)).then(setCaps).finally(() => setCapsLoading(false)),
      import('@/lib/api').then(({ aiAPI }) => aiAPI.getModelConfig().catch(() => null)).then(r => {
        const c = r?.config || {}
        setMc({
          base_url: c.base_url || '',
          api_key: '', // 不回显 key，只在填写时提交
          llm_model: c.llm_model || '',
          tts_model: c.tts_model || '',
          asr_model: c.asr_model || '',
          image_model: c.image_model || '',
          video_model: c.video_model || '',
          tts_voice: c.tts_voice || '',
        })
        setMcLoaded(true)
      }),
    ])
  }, [])

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

  const handleModelSave = async () => {
    setMcMsg(''); setMcTest('')
    setMcSaving(true)
    try {
      const { aiAPI } = await import('@/lib/api')
      const patch: Record<string, string> = {}
      if (mc.base_url.trim()) patch.base_url = mc.base_url.trim()
      if (mc.api_key.trim()) patch.api_key = mc.api_key.trim()
      if (mc.llm_model.trim()) patch.llm_model = mc.llm_model.trim()
      if (mc.tts_model.trim()) patch.tts_model = mc.tts_model.trim()
      if (mc.asr_model.trim()) patch.asr_model = mc.asr_model.trim()
      if (mc.image_model.trim()) patch.image_model = mc.image_model.trim()
      if (mc.video_model.trim()) patch.video_model = mc.video_model.trim()
      if (mc.tts_voice.trim()) patch.tts_voice = mc.tts_voice.trim()
      await aiAPI.updateModelConfig(patch)
      setMcMsg('模型配置已保存')
      setMc(prev => ({ ...prev, api_key: '' }))
      // 重新探测能力
      const { aiAPI: api2 } = await import('@/lib/api')
      api2.capabilities().then(setCaps).catch(() => setCaps(null))
    } catch (e) {
      setMcMsg('保存失败：' + (e instanceof Error ? e.message : '未知'))
    } finally { setMcSaving(false) }
  }

  const handleModelTest = async () => {
    setMcTest('')
    try {
      const { aiAPI } = await import('@/lib/api')
      const caps = await aiAPI.capabilities()
      if (caps.configured) {
        const c = Object.entries(caps.capabilities || {}).filter(([, v]) => v).map(([k]) => caps.labels?.[k] || k).join('、')
        setMcTest('连接成功，检测到能力：' + (c || '无'))
      } else {
        setMcTest('连接失败：' + (caps.message || '请检查配置'))
      }
    } catch (e) {
      setMcTest('测试失败：' + (e instanceof Error ? e.message : '未知'))
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

      {/* 模型配置 */}
      <div className="glass-card p-6 mt-6">
        <h2 className="text-sm font-bold text-gray-700 mb-1">模型配置</h2>
        <p className="text-xs text-gray-400 mb-4">
          在此接入你的模型端点（OpenAI 兼容）。保存后 AI 功能将使用这里配置的模型；留空的字段沿用环境变量默认值。
        </p>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="API 地址 (base_url)" value={mc.base_url} onChange={v => setMc(s => ({ ...s, base_url: v }))} ph="https://api.example.com/v1" />
          <Field label="API Key" value={mc.api_key} onChange={v => setMc(s => ({ ...s, api_key: v }))} ph="留空保持不变" password />
          <Field label="对话模型 (llm_model)" value={mc.llm_model} onChange={v => setMc(s => ({ ...s, llm_model: v }))} ph="如 Qwen3.6-27B / gpt-4o-mini" />
          <Field label="语音合成模型 (tts_model)" value={mc.tts_model} onChange={v => setMc(s => ({ ...s, tts_model: v }))} ph="自动探测，可留空" />
          <Field label="语音转写模型 (asr_model)" value={mc.asr_model} onChange={v => setMc(s => ({ ...s, asr_model: v }))} ph="自动探测，可留空" />
          <Field label="文生图模型 (image_model)" value={mc.image_model} onChange={v => setMc(s => ({ ...s, image_model: v }))} ph="自动探测，可留空" />
          <Field label="配音音色 (tts_voice)" value={mc.tts_voice} onChange={v => setMc(s => ({ ...s, tts_voice: v }))} ph="如 default / alloy" />
        </div>
        <div className="flex items-center gap-3 mt-4">
          <button className="btn-primary" onClick={handleModelSave} disabled={mcSaving}>
            {mcSaving ? <><Loader2 className="w-4 h-4 animate-spin" /> 保存中</> : <><Save className="w-4 h-4" /> 保存配置</>}
          </button>
          <button className="btn-secondary" onClick={handleModelTest}>
            <CheckCircle className="w-4 h-4" /> 测试连接
          </button>
          {mcMsg && <span className={`text-xs ${mcMsg.startsWith('保存失败') ? 'text-red-500' : 'text-emerald-600'}`}>{mcMsg}</span>}
          {mcTest && <span className="text-xs text-gray-500">{mcTest}</span>}
        </div>
      </div>

      {/* 模型能力 */}
      <div className="glass-card p-6 mt-6">
        <h2 className="text-sm font-bold text-gray-700 mb-1">模型能力</h2>
        <p className="text-xs text-gray-400 mb-4">
          自动探测当前接入的模型端点支持哪些能力。功能不可用时会自动降级并提示。
        </p>
        {capsLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" /> 探测中...
          </div>
        ) : !caps || !caps.configured ? (
          <p className="text-sm text-amber-600">未配置模型端点，AI 相关功能将使用降级模式。</p>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {Object.entries(caps.capabilities || {})
                .filter(([, v]) => v)
                .map(([k]) => (
                  <span key={k} className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-100">
                    <CheckCircle className="w-3.5 h-3.5" /> {caps.labels?.[k] || k}
                  </span>
                ))}
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              {Object.entries(caps.features || {}).map(([feat, avail]) => (
                <div key={feat} className="flex items-center justify-between border-b border-gray-50 py-1">
                  <span>{caps.feature_labels?.[feat] || feat}</span>
                  {avail ? (
                    <span className="text-emerald-600">可用</span>
                  ) : (
                    <span className="text-amber-600" title={(caps.missing?.[feat] || []).join('、')}>
                      需：{(caps.missing?.[feat] || []).join('、')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

function Field({ label, value, onChange, ph, password }: {
  label: string; value: string; onChange: (v: string) => void; ph?: string; password?: boolean
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input type={password ? 'password' : 'text'} className="input-field" placeholder={ph || ''} value={value} onChange={e => onChange(e.target.value)} />
    </div>
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
    <div className="w-20 h-20 rounded-full bg-brand-600 flex items-center justify-center text-white text-2xl font-bold border-2 border-white shadow-md">
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
