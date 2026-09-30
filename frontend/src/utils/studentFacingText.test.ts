import { expect, test } from 'vitest'

import { studentFacingNotes, studentFacingText } from './studentFacingText'

test('removes occupational-database and method jargon from student copy', () => {
  expect(studentFacingText('related O*NET features')).toBe('related features')
  expect(studentFacingText('was among the nearest O*NET occupation profiles to your assessment.')).toBe(
    'was among the closest career matches to your assessment.',
  )
  expect(
    studentFacingText('Scores are O*NET profile similarity, not predicted job success or accuracy.'),
  ).toBe('These scores show how closely a career matches your answers. They do not predict job success.')
  expect(studentFacingText('k-nearest neighbours using weighted-block cosine similarity')).toBe(
    'using how closely they match your answers',
  )
})

test('studentFacingNotes drops empty and duplicate rewritten notes', () => {
  expect(
    studentFacingNotes([
      'Scores are O*NET profile similarity, not predicted job success or accuracy.',
      'Scores are O*NET profile similarity, not predicted job success or accuracy.',
    ]),
  ).toEqual(['These scores show how closely a career matches your answers. They do not predict job success.'])
})
