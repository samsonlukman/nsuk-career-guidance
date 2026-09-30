import { apiRequest } from './client'
import type {
  ExperienceEvaluationCreateRequest,
  ExperienceEvaluationOut,
  RatingCreateRequest,
  RatingOut,
  RecommendationRun,
} from '../types/recommendations'

export function fetchRecommendationRun(runId: string): Promise<RecommendationRun> {
  return apiRequest<RecommendationRun>(`/api/v1/recommendations/${runId}`)
}

export function submitRecommendationRating(itemId: string, payload: RatingCreateRequest): Promise<RatingOut> {
  return apiRequest<RatingOut>(`/api/v1/recommendations/${itemId}/rating`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchExperienceEvaluation(runId: string): Promise<ExperienceEvaluationOut> {
  return apiRequest<ExperienceEvaluationOut>(`/api/v1/recommendations/${runId}/experience-evaluation`)
}

export function submitExperienceEvaluation(
  runId: string,
  payload: ExperienceEvaluationCreateRequest,
): Promise<ExperienceEvaluationOut> {
  return apiRequest<ExperienceEvaluationOut>(`/api/v1/recommendations/${runId}/experience-evaluation`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
