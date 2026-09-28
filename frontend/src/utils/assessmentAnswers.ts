import type {
  AnswerMap,
  AssessmentCreateRequest,
  Question,
  QuestionAnswer,
  SparseAnswer,
} from '../types/questionnaire'
import { isRatingType, isSparseType, optionLabel } from './questionnaire'

export const DRAFT_STORAGE_PREFIX = 'nsuk.assessment.draft.v1.'
const draftMemory = new Map<string, string>()

function readStore(key: string): string | null {
  const remembered = draftMemory.get(key)
  if (remembered !== undefined) return remembered
  try {
    if (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function') {
      return localStorage.getItem(key)
    }
  } catch {
    return null
  }
  return null
}

function writeStore(key: string, value: string): void {
  draftMemory.set(key, value)
  try {
    if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
      localStorage.setItem(key, value)
    }
  } catch {
    // In-memory copy is enough for this session.
  }
}

function deleteStore(key: string): void {
  draftMemory.delete(key)
  try {
    if (typeof localStorage !== 'undefined' && typeof localStorage.removeItem === 'function') {
      localStorage.removeItem(key)
    }
  } catch {
    // Ignore.
  }
}

export function resetDraftMemory(): void {
  draftMemory.clear()
}

export type AssessmentDraft = {
  questionnaireVersion: string
  stepIndex: number
  answers: AnswerMap
  updatedAt: string
}

export function assessmentDraftKey(userId: string): string {
  return `${DRAFT_STORAGE_PREFIX}${userId}`
}

export function hasAssessmentDraft(userId: string): boolean {
  return readStore(assessmentDraftKey(userId)) !== null
}

export function loadAssessmentDraft(userId: string, questionnaireVersion: string): AssessmentDraft | null {
  const raw = readStore(assessmentDraftKey(userId))
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as AssessmentDraft
    if (!parsed || parsed.questionnaireVersion !== questionnaireVersion || !parsed.answers) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function saveAssessmentDraft(userId: string, draft: AssessmentDraft): void {
  writeStore(assessmentDraftKey(userId), JSON.stringify(draft))
}

export function clearAssessmentDraft(userId: string): void {
  deleteStore(assessmentDraftKey(userId))
}

export function selectedCount(answer: QuestionAnswer | undefined): number {
  if (!answer || answer.kind !== 'selections') return 0
  return answer.selections.length
}

export function canSelectAnother(question: Question, answer: QuestionAnswer | undefined): boolean {
  const maximum = question.max_selections
  if (maximum == null) return true
  return selectedCount(answer) < maximum
}

export function validateQuestion(question: Question, answer: QuestionAnswer | undefined): string | null {
  if (isSparseType(question.response_type)) {
    return validateSparse(question, answer)
  }

  const value = answer?.kind === 'value' ? answer.value.trim() : ''
  if (!value) {
    return question.is_required ? 'This question is required.' : null
  }

  if (question.response_type === 'choice') {
    const allowed = new Set(question.options.map((option) => option.value))
    if (allowed.size > 0 && !allowed.has(value)) {
      return 'Choose one of the listed options.'
    }
    return null
  }

  if (isRatingType(question.response_type)) {
    return validateRatingValue(question, value, true)
  }

  return null
}

function validateRatingValue(question: Question, raw: string, matchOptions: boolean): string | null {
  const number = Number(raw)
  if (!Number.isInteger(number)) {
    return 'Choose a whole-number rating.'
  }
  const minimum = question.min_value
  const maximum = question.max_value
  if (minimum != null && maximum != null && (number < minimum || number > maximum)) {
    return `Choose a rating from ${minimum} to ${maximum}.`
  }
  if (matchOptions) {
    const allowed = new Set(question.options.map((option) => option.value))
    if (allowed.size > 0 && !allowed.has(raw)) {
      return `Choose a rating from ${minimum ?? 1} to ${maximum ?? 7}.`
    }
  }
  return null
}

function validateSparse(question: Question, answer: QuestionAnswer | undefined): string | null {
  const selections = answer?.kind === 'selections' ? answer.selections : []
  const minimum = question.min_selections ?? (question.is_required ? 1 : 0)
  const maximum = question.max_selections
  if (selections.length < minimum) {
    return minimum === 1
      ? 'Select at least one area, then rate it.'
      : `Select at least ${minimum} areas, then rate each one.`
  }
  if (maximum != null && selections.length > maximum) {
    return `Select at most ${maximum} areas.`
  }
  const unrated = selections.filter((item) => item.value == null)
  if (unrated.length > 0) {
    return 'Rate every selected area before continuing.'
  }
  for (const item of selections) {
    if (item.value == null) continue
    const ratingError = validateRatingValue(question, String(item.value), false)
    if (ratingError) return ratingError
  }
  return null
}

export function unansweredRequired(questions: Question[], answers: AnswerMap): Question[] {
  return questions.filter((question) => validateQuestion(question, answers[question.code]) !== null && question.is_required)
}

export function incompleteQuestions(questions: Question[], answers: AnswerMap): Question[] {
  return questions.filter((question) => validateQuestion(question, answers[question.code]) !== null)
}

export function toSubmissionPayload(
  questionnaireVersion: string,
  questions: Question[],
  answers: AnswerMap,
): AssessmentCreateRequest {
  const responses = []
  for (const question of questions) {
    const answer = answers[question.code]
    if (!answer) continue
    if (answer.kind === 'value') {
      const value = answer.value.trim()
      if (!value) continue
      responses.push({ code: question.code, value })
      continue
    }
    const rated = answer.selections.filter((item): item is { element_id: string; value: number } => item.value != null)
    if (rated.length === 0) continue
    responses.push({
      code: question.code,
      selections: rated.map((item) => ({ element_id: item.element_id, value: item.value })),
    })
  }
  return {
    questionnaire_version: questionnaireVersion,
    responses,
  }
}

export function summarizeAnswer(question: Question, answer: QuestionAnswer | undefined): string {
  if (!answer) return 'Not answered'
  if (answer.kind === 'value') {
    const value = answer.value.trim()
    if (!value) return 'Not answered'
    return optionLabel(question, value)
  }
  if (answer.selections.length === 0) return 'None selected'
  return answer.selections
    .map((item) => {
      const name = optionLabel(question, item.element_id)
      return item.value == null ? `${name} (not rated)` : `${name} — ${item.value}`
    })
    .join('; ')
}

export function toggleSparseSelection(question: Question, answer: SparseAnswer | undefined, elementId: string): SparseAnswer {
  const current = answer?.kind === 'selections' ? answer.selections : []
  const exists = current.some((item) => item.element_id === elementId)
  if (exists) {
    return { kind: 'selections', selections: current.filter((item) => item.element_id !== elementId) }
  }
  const maximum = question.max_selections
  if (maximum != null && current.length >= maximum) {
    return { kind: 'selections', selections: current }
  }
  return { kind: 'selections', selections: [...current, { element_id: elementId, value: null }] }
}

export function rateSparseSelection(answer: SparseAnswer | undefined, elementId: string, value: number): SparseAnswer {
  const current = answer?.kind === 'selections' ? answer.selections : []
  return {
    kind: 'selections',
    selections: current.map((item) => (item.element_id === elementId ? { ...item, value } : item)),
  }
}

export function submissionErrorMessage(error: { status?: number; code?: string; message?: string }): string {
  if (error.status === 401 || error.code === 'unauthenticated') {
    return 'Your session has expired. Log in again. Your answers are still saved on this device.'
  }
  if (error.code === 'network_error') {
    return error.message ?? 'Unable to reach the server. Your answers are still saved on this device.'
  }
  if (error.code === 'missing_required_response') {
    return 'Some required answers are missing. Use the review list to complete them.'
  }
  if (error.code === 'incomplete_assessment') {
    return 'A required selection is incomplete. Check the interest and knowledge sections.'
  }
  if (error.code === 'invalid_response' || error.code === 'validation_error') {
    return 'One or more answers are outside the allowed range. Review your ratings and selections.'
  }
  const detail = error.message || 'The assessment could not be submitted.'
  return `${detail} Your answers are still saved on this device.`
}
