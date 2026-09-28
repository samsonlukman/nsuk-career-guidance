import { describe, expect, test } from 'vitest'

import { mockQuestionnaire } from '../test/questionnaireFixture'
import { ratingScaleOptions } from './questionnaire'
import {
  canSelectAnother,
  incompleteQuestions,
  toggleSparseSelection,
  toSubmissionPayload,
  validateQuestion,
} from './assessmentAnswers'

const byCode = Object.fromEntries(mockQuestionnaire.questions.map((question) => [question.code, question]))

describe('assessment validation', () => {
  test('requires a choice on required questions', () => {
    expect(validateQuestion(byCode.level, undefined)).toBe('This question is required.')
    expect(validateQuestion(byCode.level, { kind: 'value', value: '200' })).toBeNull()
  })

  test('allows a blank optional text answer', () => {
    expect(validateQuestion(byCode.department, { kind: 'value', value: '' })).toBeNull()
  })

  test('rejects ratings outside the permitted range', () => {
    expect(validateQuestion(byCode.interest_realistic, { kind: 'value', value: '9' })).toMatch(/1 to 7/)
    expect(validateQuestion(byCode.interest_realistic, { kind: 'value', value: '4' })).toBeNull()
  })

  test('enforces SIA selection limits and ratings', () => {
    const sia = byCode.sia
    expect(validateQuestion(sia, { kind: 'selections', selections: [] })).toMatch(/at least one/)
    const five = ['1.B.3.a', '1.B.3.b', '1.B.3.c', '1.B.3.d', '1.B.3.e'].map((id) => ({
      element_id: id,
      value: 6 as number | null,
    }))
    expect(validateQuestion(sia, { kind: 'selections', selections: five })).toBeNull()
    expect(canSelectAnother(sia, { kind: 'selections', selections: five })).toBe(false)
    const blocked = toggleSparseSelection(sia, { kind: 'selections', selections: five }, '1.B.3.f')
    expect(blocked.selections).toHaveLength(5)
    expect(
      validateQuestion(sia, { kind: 'selections', selections: [{ element_id: '1.B.3.a', value: null }] }),
    ).toMatch(/Rate every selected/)
  })

  test('does not zero-fill unselected sparse elements in the payload', () => {
    const payload = toSubmissionPayload('questionnaire_v1', mockQuestionnaire.questions, {
      level: { kind: 'value', value: '300' },
      sia: { kind: 'selections', selections: [{ element_id: '1.B.3.b', value: 7 }] },
    })
    const sia = payload.responses.find((item) => item.code === 'sia')
    expect(sia?.selections).toEqual([{ element_id: '1.B.3.b', value: 7 }])
    expect(payload.responses.find((item) => item.code === 'department')).toBeUndefined()
  })

  test('builds a numeric rating scale for sparse-select questions', () => {
    const siaScale = ratingScaleOptions(byCode.sia).map((option) => option.value)
    expect(siaScale).toEqual(['1', '2', '3', '4', '5', '6', '7'])
    const knowledgeScale = ratingScaleOptions(byCode.knowledge).map((option) => option.value)
    expect(knowledgeScale).toEqual(['1', '2', '3', '4', '5'])
  })

  test('lists incomplete required questions for the review screen', () => {
    const missing = incompleteQuestions(mockQuestionnaire.questions, {
      level: { kind: 'value', value: '100' },
    })
    expect(missing.map((item) => item.code)).toEqual([
      'interest_realistic',
      'sia',
      'knowledge',
      'pref_indoor',
    ])
  })
})
