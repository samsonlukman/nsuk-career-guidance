export type FeatureContribution = {
  block: string
  element_id: string
  element_name: string
  student_raw: number | null
  student_normalized: number | null
  occupation_raw: number | null
  occupation_normalized: number | null
  note: string
}

export type RuleFlag = {
  rule_code: string
  action: string
  reason: string
  penalty: number | null
  element_id: string | null
  domain: string | null
}

export type RecommendationItem = {
  id: string
  rank: number
  onetsoc_code: string
  title: string
  job_zone: number | null
  distance: number
  raw_similarity: number
  recommendation_score: number
  explanation: string
  job_zone_note: string | null
  work_activities: string[]
  contributing_features: FeatureContribution[]
  rule_flags: RuleFlag[]
  penalties: RuleFlag[]
}

export type RecommendationRun = {
  id: string
  assessment_id: string
  created_at: string
  k: number
  metric: string
  eligible_count: number
  elapsed_ms: number | null
  feature_version: string
  onet_release: string | null
  onet_snapshot_id: string
  questionnaire_version: string
  config_version: string
  block_weights: Record<string, number>
  notes: string[]
  items: RecommendationItem[]
}

export type OccupationEducationItem = {
  category: string
  description: string
  percent: number
}

export type OccupationActivityItem = {
  element_id: string
  name: string
  importance: number | null
}

export type OccupationFeatureItem = {
  element_id: string
  element_name: string
  value: number | null
}

export type OccupationDetail = {
  onetsoc_code: string
  title: string
  description: string
  job_zone: number | null
  knn_complete: boolean
  recommendable: boolean
  has_education: boolean
  has_work_context: boolean
  feature_version: string
  onet_release: string
  job_zone_name: string | null
  job_zone_education: string | null
  job_zone_experience: string | null
  feature_count: number
  education: OccupationEducationItem[]
  work_activities: OccupationActivityItem[]
  interests: OccupationFeatureItem[]
}

export type RatingCreateRequest = {
  relevance_1_to_5: number
  comment?: string | null
}

export type RatingOut = {
  id: string
  item_id: string
  relevance_1_to_5: number
  comment: string | null
  created_at: string
  note: string
}

export type ExperienceEvaluationCreateRequest = {
  questions_easy_to_understand: number
  assessment_easy_to_complete: number
  system_easy_to_navigate: number
  recommendations_easy_to_understand: number
  explanations_helped: number
  reflected_interests: number
  reflected_skills: number
  helped_explore_options: number
  would_use_again: number
  would_discuss_with_counsellor: number
  liked_most_and_improvement?: string | null
}

export type ExperienceEvaluationOut = ExperienceEvaluationCreateRequest & {
  id: string
  run_id: string
  student_user_id: string
  liked_most_and_improvement: string | null
  created_at: string
  note: string
}
