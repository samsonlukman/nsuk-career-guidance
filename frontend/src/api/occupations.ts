import { apiRequest } from './client'
import type { OccupationDetail } from '../types/recommendations'

export function fetchOccupation(socCode: string): Promise<OccupationDetail> {
  return apiRequest<OccupationDetail>(`/api/v1/occupations/${encodeURIComponent(socCode)}`)
}
