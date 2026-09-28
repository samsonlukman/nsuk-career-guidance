import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { fetchCurrentUser, loginAccount, logoutAccount, registerAccount } from '../api/auth'
import { ApiError } from '../api/client'
import type { CurrentUser, LoginPayload, RegisterPayload } from '../types/auth'

export type AuthContextValue = {
  user: CurrentUser | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  login: (payload: LoginPayload) => Promise<CurrentUser>
  register: (payload: RegisterPayload) => Promise<CurrentUser>
  logout: () => Promise<void>
  setUser: (user: CurrentUser | null) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setError(null)
    try {
      const current = await fetchCurrentUser()
      setUser(current)
    } catch (err) {
      setUser(null)
      if (!(err instanceof ApiError && err.status === 401)) {
        setError(err instanceof ApiError ? err.message : 'Unable to verify your session.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const login = useCallback(async (payload: LoginPayload) => {
    const current = await loginAccount(payload)
    setUser(current)
    setError(null)
    return current
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    const current = await registerAccount(payload)
    setUser(current)
    setError(null)
    return current
  }, [])

  const logout = useCallback(async () => {
    await logoutAccount()
    setUser(null)
    setError(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, error, refresh, login, register, logout, setUser }),
    [user, loading, error, refresh, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
