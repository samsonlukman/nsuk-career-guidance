export type ApiErrorBody = {
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export type ProfileOptions = {
  faculties: string[]
  levels: string[]
  further_study: string[]
  course_relatedness: string[]
}

export type RecommendationHistoryItem = {
  run_id: string
  created_at: string
  k: number
  feature_version: string
  questionnaire_version: string
  config_version: string
  onet_release: string | null
  eligible_count: number
  item_count: number
  top_occupation_title: string | null
  top_onetsoc_code: string | null
}

export type AssessmentSummary = {
  id: string
  status: string
  questionnaire_version: string | null
  feature_version: string
  started_at: string
  completed_at: string | null
}

export type Dashboard = {
  user: import('./auth').CurrentUser
  has_completed_assessment: boolean
  latest_assessment: AssessmentSummary | null
  latest_recommendation: RecommendationHistoryItem | null
  recommendation_history: RecommendationHistoryItem[]
}
