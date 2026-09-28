import type { Questionnaire } from '../types/questionnaire'
import { apiRequest } from './client'

export function fetchActiveQuestionnaire(): Promise<Questionnaire> {
  return apiRequest<Questionnaire>('/api/v1/questionnaires/active')
}
