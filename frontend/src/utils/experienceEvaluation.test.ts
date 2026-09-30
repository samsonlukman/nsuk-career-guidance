import { expect, test } from 'vitest'

import { EMPTY_EXPERIENCE_ANSWERS, missingExperienceFields } from './experienceEvaluation'

test('missingExperienceFields lists unanswered scale items', () => {
  expect(missingExperienceFields(EMPTY_EXPERIENCE_ANSWERS)).toHaveLength(10)
  expect(
    missingExperienceFields({
      ...EMPTY_EXPERIENCE_ANSWERS,
      questions_easy_to_understand: 4,
      assessment_easy_to_complete: 4,
      system_easy_to_navigate: 4,
      recommendations_easy_to_understand: 4,
      explanations_helped: 4,
      reflected_interests: 4,
      reflected_skills: 4,
      helped_explore_options: 4,
      would_use_again: 4,
      would_discuss_with_counsellor: 4,
    }),
  ).toEqual([])
})
