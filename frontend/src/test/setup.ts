import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

import { resetDraftMemory } from '../utils/assessmentAnswers'
import { resetExperienceEvaluationPrompts } from '../utils/experienceEvaluationPrompt'

afterEach(() => {
  cleanup()
  resetDraftMemory()
  resetExperienceEvaluationPrompts()
})
