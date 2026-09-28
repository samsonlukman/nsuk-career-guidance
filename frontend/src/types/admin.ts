export type PageMeta = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type AdminSnapshotSummary = {
  snapshot_id: string | null
  onet_release: string | null
  onet_release_month: string | null
  feature_version: string | null
  occupation_count: number
  recommendable_count: number
  knn_feature_count: number
}

export type AdminQuestionnaireSummary = {
  version: string | null
  status: string | null
  feature_version: string | null
  question_count: number
  option_count: number
}

export type AdminConfigSummary = {
  version: string | null
  k: number | null
  metric: string | null
  feature_version: string | null
  block_weights: Record<string, number>
}

export type AdminSystemStatus = {
  api: string
  database: string
  active_onet_snapshot: boolean
  active_questionnaire: boolean
  active_recommendation_config: boolean
}

export type AdminDashboard = {
  students_total: number
  assessments_completed: number
  recommendation_runs: number
  ratings_total: number
  ratings_average: number | null
  active_onet: AdminSnapshotSummary
  active_questionnaire: AdminQuestionnaireSummary
  active_config: AdminConfigSummary
  system: AdminSystemStatus
  notes: string[]
}

export type AdminStudentListItem = {
  id: string
  email: string
  is_active: boolean
  created_at: string
  last_login_at: string | null
  first_name: string | null
  last_name: string | null
  matric_number: string | null
  faculty: string | null
  department: string | null
  level: string | null
  latest_assessment_status: string | null
  latest_assessment_completed_at: string | null
  recommendation_run_count: number
}

export type AdminStudentList = PageMeta & {
  items: AdminStudentListItem[]
}

export type AdminStudentProfile = {
  first_name: string | null
  last_name: string | null
  matric_number: string | null
  faculty: string | null
  department: string | null
  level: string | null
  further_study: string | null
  course_relatedness: string | null
}

export type AdminStudentAssessment = {
  id: string
  status: string
  questionnaire_version: string | null
  feature_version: string
  started_at: string
  completed_at: string | null
}

export type AdminRecommendationHistoryItem = {
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

export type AdminStudentDetail = {
  id: string
  email: string
  is_active: boolean
  created_at: string
  last_login_at: string | null
  profile: AdminStudentProfile
  assessments: AdminStudentAssessment[]
  recommendation_history: AdminRecommendationHistoryItem[]
}

export type AdminRunListItem = {
  run_id: string
  student_id: string
  student_email: string
  student_name: string | null
  assessment_id: string
  assessment_completed_at: string | null
  created_at: string
  onet_release: string | null
  questionnaire_version: string
  config_version: string
  feature_version: string
  item_count: number
  top_occupation_title: string | null
  top_onetsoc_code: string | null
}

export type AdminRunList = PageMeta & {
  items: AdminRunListItem[]
}

export type AdminStudentRef = {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
}

export type AdminRunDetail = {
  student: AdminStudentRef
  run: import('./recommendations').RecommendationRun
}

export type AdminRatingListItem = {
  id: string
  relevance_1_to_5: number
  comment: string | null
  created_at: string
  occupation_title: string | null
  onetsoc_code: string
  run_id: string
  student_id: string
  student_email: string
}

export type AdminRatingSummary = {
  ratings_total: number
  average_relevance: number | null
  distribution: Record<string, number>
  note: string
}

export type AdminRatingList = PageMeta & {
  items: AdminRatingListItem[]
  summary: AdminRatingSummary
}

export type AdminJobZoneInfo = {
  job_zone: number
  name: string
  education: string | null
  occupation_count: number
  recommendable_count: number
}

export type AdminOnetSnapshot = AdminSnapshotSummary & {
  job_zones: AdminJobZoneInfo[]
  note: string
}

export type AdminQuestionInspect = {
  code: string
  section: string
  prompt: string
  response_type: string
  block: string | null
  onet_element_id: string | null
  sort_order: number
  is_required: boolean
  option_count: number
}

export type AdminQuestionnaire = AdminQuestionnaireSummary & {
  questions: AdminQuestionInspect[]
  note: string
}

export type AdminRecommendationConfig = AdminConfigSummary & {
  note: string
}

export type AdminHealth = {
  api: string
  database: string
  active_onet_snapshot: boolean
  active_questionnaire: boolean
  active_recommendation_config: boolean
  feature_version: string | null
  questionnaire_version: string | null
  config_version: string | null
}

export type KnowledgeElement = {
  element_id: string
  element_name: string
}

export type FacultyKnowledgeCatalog = {
  faculties: string[]
  knowledge_elements: KnowledgeElement[]
  note: string
}

export type FacultyKnowledgePrior = {
  id: number
  faculty: string
  element_id: string
  element_name: string | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export type FacultyKnowledgePriorList = {
  items: FacultyKnowledgePrior[]
}

export type FacultyKnowledgePriorWrite = {
  faculty: string
  element_id: string
}

export type FacultyKnowledgePriorAudit = {
  id: string
  prior_id: number | null
  action: string
  faculty: string
  element_id: string
  element_name: string | null
  previous_faculty: string | null
  previous_element_id: string | null
  previous_element_name: string | null
  actor_user_id: string | null
  actor_email: string | null
  created_at: string
}

export type FacultyKnowledgePriorAuditList = PageMeta & {
  items: FacultyKnowledgePriorAudit[]
}
