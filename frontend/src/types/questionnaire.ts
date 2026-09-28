export type QuestionOption = {
  value: string
  label: string
  onet_element_id: string | null
  sort_order: number
}

export type QuestionResponseType = 'choice' | 'text' | 'likert' | 'sparse_select' | 'preference'

export type Question = {
  code: string
  section: string
  prompt: string
  response_type: string
  block: string | null
  onet_element_id: string | null
  onet_scale_id: string | null
  sort_order: number
  is_required: boolean
  min_value: number | null
  max_value: number | null
  min_selections: number | null
  max_selections: number | null
  options: QuestionOption[]
}

export type Questionnaire = {
  version: string
  feature_version: string
  status: string
  questions: Question[]
}

export type SparseSelection = {
  element_id: string
  value: number
}

export type AssessmentResponsePayload = {
  code: string
  value?: string | number | null
  selections?: SparseSelection[]
}

export type AssessmentCreateRequest = {
  questionnaire_version: string
  responses: AssessmentResponsePayload[]
}

export type AssessmentSubmitConfirmation = {
  id: string
  assessment_id: string
  created_at: string
  questionnaire_version: string
  feature_version: string
  config_version: string
  k: number
  item_count: number
}

export type ScalarAnswer = {
  kind: 'value'
  value: string
}

export type SparseAnswer = {
  kind: 'selections'
  selections: Array<{
    element_id: string
    value: number | null
  }>
}

export type QuestionAnswer = ScalarAnswer | SparseAnswer

export type AnswerMap = Record<string, QuestionAnswer>
