import type { AssessmentCreateRequest, AssessmentSubmitConfirmation } from '../types/questionnaire'
import { apiRequest } from './client'

type RecommendationRunResponse = AssessmentSubmitConfirmation & {
  items?: Array<unknown>
}

export async function submitAssessment(payload: AssessmentCreateRequest): Promise<AssessmentSubmitConfirmation> {
  const run = await apiRequest<RecommendationRunResponse>('/api/v1/assessments', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  return {
    id: run.id,
    assessment_id: run.assessment_id,
    created_at: run.created_at,
    questionnaire_version: run.questionnaire_version,
    feature_version: run.feature_version,
    config_version: run.config_version,
    k: run.k,
    item_count: Array.isArray(run.items) ? run.items.length : 0,
  }
}
