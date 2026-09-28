import type { Dashboard } from '../types/api'
import type { CurrentUser, ProfileUpdatePayload } from '../types/auth'
import { apiRequest } from './client'

export function fetchDashboard(): Promise<Dashboard> {
  return apiRequest<Dashboard>('/api/v1/me/dashboard')
}

export function updateProfile(payload: ProfileUpdatePayload): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/v1/me/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}
