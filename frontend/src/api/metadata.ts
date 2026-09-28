import type { ProfileOptions } from '../types/api'
import { apiRequest } from './client'

export function fetchProfileOptions(): Promise<ProfileOptions> {
  return apiRequest<ProfileOptions>('/api/v1/metadata/profile-options')
}
