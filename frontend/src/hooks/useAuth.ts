'use client'

import { useState, useEffect, useCallback } from 'react'
import { auth } from '@/lib/api'

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  is_active: boolean
  created_at: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

export function useAuth(): AuthState {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const response = await auth.getMe()
      setUser(response.data)
    } catch {
      setUser(null)
      if (typeof window !== 'undefined') {
        localStorage.removeItem('mcp_token')
      }
      setToken(null)
    }
  }, [])

  useEffect(() => {
    const storedToken = typeof window !== 'undefined'
      ? localStorage.getItem('mcp_token')
      : null

    if (storedToken) {
      setToken(storedToken)
      refreshUser().finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const response = await auth.login(email, password)
    const { access_token, user: userData } = response.data

    localStorage.setItem('mcp_token', access_token)
    setToken(access_token)
    setUser(userData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('mcp_token')
    setToken(null)
    setUser(null)
    window.location.href = '/login'
  }, [])

  return {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    login,
    logout,
    refreshUser,
  }
}
