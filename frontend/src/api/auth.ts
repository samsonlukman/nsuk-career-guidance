import type { CurrentUser, LoginPayload, RegisterPayload } from '../types/auth'
import { apiRequest } from './client'

export function registerAccount(payload: RegisterPayload): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function loginAccount(payload: LoginPayload): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function logoutAccount(): Promise<{ status: string }> {
  return apiRequest<{ status: string }>('/api/v1/auth/logout', { method: 'POST' })
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/v1/auth/me')
}
