'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Mail, Lock, User, Loader2, ArrowRight, Eye, EyeOff, Brain } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { ApiError } from '@/lib/api'

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(email, username, password, displayName || undefined)
      router.push('/chat')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-aurora bg-grid flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        
        <div className="flex justify-center mb-5">
          <span className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg">
            <Brain className="w-7 h-7 text-white" />
          </span>
        </div>
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">注册 EduAgent</h1>
          <p className="text-sm text-gray-500 mt-1">开始跟 AI 学习编程</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-6 space-y-4">
          <div>
            <label className="label">邮箱</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="email"
                className="input-field pl-10"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="label">用户名</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                className="input-field pl-10"
                placeholder="至少 2 个字符"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                minLength={2}
              />
            </div>
          </div>

          <div>
            <label className="label">昵称（可选）</label>
            <input
              type="text"
              className="input-field"
              placeholder="显示名称"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </div>

          <div>
            <label className="label">密码</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                className="input-field pl-10 pr-10"
                placeholder="至少 8 位"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label={showPassword ? '隐藏密码' : '显示密码'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> 注册中
              </>
            ) : (
              <>
                注册 <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <p className="text-center text-sm text-gray-400">
            已有账号？{' '}
            <Link href="/login" className="text-brand-600 hover:underline">
              登录
            </Link>
          </p>
        </form>
      </div>
    </main>
  )
}
