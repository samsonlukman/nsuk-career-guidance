import { apiRequest } from './client'
import type { RatingCreateRequest, RatingOut, RecommendationRun } from '../types/recommendations'

export function fetchRecommendationRun(runId: string): Promise<RecommendationRun> {
  return apiRequest<RecommendationRun>(`/api/v1/recommendations/${runId}`)
}

export function submitRecommendationRating(itemId: string, payload: RatingCreateRequest): Promise<RatingOut> {
  return apiRequest<RatingOut>(`/api/v1/recommendations/${itemId}/rating`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
