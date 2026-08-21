'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import {
  authAPI,
  getToken,
  setToken,
  getStoredUser,
  setStoredUser,
  clearAuth,
  type User,
} from '@/lib/api'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, displayName?: string) => Promise<void>
  logout: () => void
  updateUser: (user: User) => void
}

const AuthContext = createContext<AuthContextValue>(null!)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    const stored = getStoredUser()
    if (token && stored) {
      setUser(stored)
      // 验证 token 是否有效
      authAPI
        .getMe()
        .then((u) => {
          setUser(u)
          setStoredUser(u)
        })
        .catch(() => {
          clearAuth()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await authAPI.login(email, password)
    setToken(res.access_token)
    setStoredUser(res.user)
    setUser(res.user)
  }, [])

  const register = useCallback(
    async (email: string, username: string, password: string, displayName?: string) => {
      const res = await authAPI.register({
        email,
        username,
        password,
        display_name: displayName,
      })
      setToken(res.access_token)
      setStoredUser(res.user)
      setUser(res.user)
    },
    [],
  )

  const logout = useCallback(() => {
    clearAuth()
    setUser(null)
  }, [])

  const updateUser = useCallback((u: User) => {
    setStoredUser(u)
    setUser(u)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
