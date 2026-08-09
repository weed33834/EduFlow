'use client'

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import {
  authAPI,
  getToken,
  setToken,
  getStoredUser,
  setStoredUser,
  clearAuth,
  type User,
} from '@/lib/api'

interface RegisterPayload {
  email: string
  username: string
  password: string
  display_name?: string
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  register: (data: RegisterPayload) => Promise<User>
  logout: () => void
  updateUser: (patch: Partial<User>) => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // 初始化：检查 token 有效性
  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }

    const storedUser = getStoredUser()

    const init = async () => {
      try {
        const me = await authAPI.getMe()
        // 后端 /auth/me 可能返回空对象，需校验
        if (me && (me as User).id) {
          setUser(me)
          setStoredUser(me)
        } else if (storedUser) {
          setUser(storedUser)
        } else {
          // token 无效且无本地用户，清理
          clearAuth()
        }
      } catch {
        // 后端 getMe 未实现或失败，回退到本地缓存用户（保持登录态）
        if (storedUser) {
          setUser(storedUser)
        } else {
          clearAuth()
        }
      } finally {
        setLoading(false)
      }
    }

    init()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await authAPI.login(email, password)
    setToken(res.access_token)
    setStoredUser(res.user)
    setUser(res.user)
    return res.user
  }, [])

  const register = useCallback(async (data: RegisterPayload) => {
    const res = await authAPI.register(data)
    setToken(res.access_token)
    setStoredUser(res.user)
    setUser(res.user)
    return res.user
  }, [])

  const logout = useCallback(() => {
    clearAuth()
    setUser(null)
  }, [])

  const updateUser = useCallback((patch: Partial<User>) => {
    setUser(prev => {
      if (!prev) return prev
      const next = { ...prev, ...patch }
      setStoredUser(next)
      return next
    })
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth 必须在 AuthProvider 内部使用')
  }
  return ctx
}
