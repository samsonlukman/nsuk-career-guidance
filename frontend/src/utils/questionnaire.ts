import type { CurrentUser } from '../types/auth'
import type { AnswerMap, Question, Questionnaire, QuestionAnswer } from '../types/questionnaire'

export const SECTION_TITLES: Record<string, string> = {
  profile: 'Profile',
  riasec: 'RIASEC',
  sia: 'Specific Interest Areas',
  essential_skills: 'Essential Skills',
  transferable_skills: 'Transferable Skills',
  work_styles: 'Work Styles',
  knowledge: 'Knowledge',
  work_preferences: 'Work Setting',
}

export function orderedQuestions(questionnaire: Questionnaire): Question[] {
  return [...questionnaire.questions].sort((left, right) => {
    if (left.sort_order !== right.sort_order) return left.sort_order - right.sort_order
    return left.code.localeCompare(right.code)
  })
}

export function sectionTitle(section: string): string {
  return SECTION_TITLES[section] ?? section.replaceAll('_', ' ')
}

export function sectionsInOrder(questions: Question[]): string[] {
  const seen: string[] = []
  for (const question of questions) {
    if (!seen.includes(question.section)) seen.push(question.section)
  }
  return seen
}

export function questionsInSection(questions: Question[], section: string): Question[] {
  return questions.filter((question) => question.section === section)
}

export function optionLabel(question: Question, value: string): string {
  return question.options.find((option) => option.value === value)?.label ?? value
}

export function sortedOptions(question: Question): Question['options'] {
  return [...question.options].sort((left, right) => {
    if (left.sort_order !== right.sort_order) return left.sort_order - right.sort_order
    return left.value.localeCompare(right.value)
  })
}

/** Likert/preference options are a numeric scale. Sparse-select options are element IDs. */
export function ratingScaleOptions(question: Question): Question['options'] {
  if (question.response_type === 'sparse_select') {
    const minimum = Math.round(question.min_value ?? 1)
    const maximum = Math.round(question.max_value ?? 7)
    return Array.from({ length: Math.max(0, maximum - minimum + 1) }, (_, index) => {
      const value = String(minimum + index)
      return { value, label: value, onet_element_id: null, sort_order: index }
    })
  }
  return sortedOptions(question)
}

export function prefillFromProfile(questions: Question[], user: CurrentUser): AnswerMap {
  const answers: AnswerMap = {}
  const profile = user.profile
  const fields: Array<keyof CurrentUser['profile']> = [
    'faculty',
    'department',
    'level',
    'further_study',
    'course_relatedness',
  ]
  for (const field of fields) {
    const value = profile[field]
    const question = questions.find((item) => item.code === field)
    if (question && value) {
      answers[field] = { kind: 'value', value }
    }
  }
  return answers
}

export function emptySparseAnswer(): QuestionAnswer {
  return { kind: 'selections', selections: [] }
}

export function isSparseType(responseType: string): boolean {
  return responseType === 'sparse_select'
}

export function isRatingType(responseType: string): boolean {
  return responseType === 'likert' || responseType === 'preference'
}
