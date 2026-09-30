import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test } from 'vitest'

import { jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'
import { mockRecommendationRun, RUN_ID } from '../test/recommendationFixture'
import type { ExperienceEvaluationOut } from '../types/recommendations'

const savedEvaluation: ExperienceEvaluationOut = {
  id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
  run_id: RUN_ID,
  student_user_id: studentUser.id,
  questions_easy_to_understand: 4,
  assessment_easy_to_complete: 5,
  system_easy_to_navigate: 4,
  recommendations_easy_to_understand: 4,
  explanations_helped: 5,
  reflected_interests: 4,
  reflected_skills: 3,
  helped_explore_options: 5,
  would_use_again: 4,
  would_discuss_with_counsellor: 5,
  liked_most_and_improvement: 'Clear explanations.',
  created_at: '2026-09-30T00:00:00Z',
  note: 'This form records your experience, usability, usefulness, and perceived relevance. It is not an accuracy test.',
}

function stubEvaluation(
  handler?: (url: string, init?: RequestInit) => Promise<Response> | Response | undefined,
) {
  return stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    const extra = handler?.(url, init)
    if (extra) return extra
    if (url.includes(`/api/v1/recommendations/${RUN_ID}/experience-evaluation`)) {
      return jsonResponse(404, {
        error: { code: 'experience_evaluation_not_found', message: 'Experience evaluation was not found' },
      })
    }
    if (url.includes(`/api/v1/recommendations/${RUN_ID}`)) {
      return jsonResponse(200, mockRecommendationRun)
    }
    return undefined
  })
}

afterEach(() => {
  restoreFetch()
})

test('shows the experience evaluation form after recommendations', async () => {
  stubEvaluation()
  renderApp(`/recommendations/${RUN_ID}/evaluate`)

  expect(await screen.findByRole('heading', { name: 'Evaluate Your Experience' })).toBeInTheDocument()
  expect(await screen.findByText(/The assessment questions were easy to understand/)).toBeInTheDocument()
  expect(screen.getByText(/not an accuracy test/i)).toBeInTheDocument()
  expect(screen.queryByText(/accuracy test of the recommendations/i)).not.toBeInTheDocument()
  expect(screen.getByText(/I would discuss the recommendations with a career counsellor/)).toBeInTheDocument()
  expect(
    screen.getByLabelText('11. What did you like most about the system, and what improvement would you suggest?'),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Submit evaluation' })).toBeInTheDocument()
})

test('requires every scaled answer before submit', async () => {
  stubEvaluation()
  const user = userEvent.setup()
  renderApp(`/recommendations/${RUN_ID}/evaluate`)
  await screen.findByRole('button', { name: 'Submit evaluation' })
  await user.click(screen.getByRole('button', { name: 'Submit evaluation' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Please answer every question on the 1 to 5 scale')
})

test('submits the experience evaluation without calling it accuracy', async () => {
  const fetchMock = stubEvaluation((url, init) => {
    if (url.includes(`/api/v1/recommendations/${RUN_ID}/experience-evaluation`) && init?.method === 'POST') {
      const body = JSON.parse(String(init.body)) as Record<string, unknown>
      expect(body.questions_easy_to_understand).toBe(4)
      expect(body.would_discuss_with_counsellor).toBe(5)
      expect(body.liked_most_and_improvement).toBe('Clear shortlist.')
      return jsonResponse(200, { ...savedEvaluation, liked_most_and_improvement: 'Clear shortlist.' })
    }
    return undefined
  })
  const user = userEvent.setup()
  renderApp(`/recommendations/${RUN_ID}/evaluate`)
  await screen.findByRole('button', { name: 'Submit evaluation' })

  for (const prompt of [
    'The assessment questions were easy to understand.',
    'The assessment was easy to complete.',
    'The system was easy to navigate.',
    'The career recommendations were easy to understand.',
    'The explanations helped me understand why the careers were recommended.',
    'The recommendations reflected my interests.',
    'The recommendations reflected my skills.',
    'The system helped me explore career options.',
    'I would use this system again for career exploration.',
    'I would discuss the recommendations with a career counsellor.',
  ]) {
    const group = screen.getByRole('radiogroup', { name: prompt })
    await user.click(group.querySelector('input[value="4"]') as HTMLInputElement)
  }
  await user.click(
    screen.getByRole('radiogroup', { name: 'I would discuss the recommendations with a career counsellor.' })
      .querySelector('input[value="5"]') as HTMLInputElement,
  )
  await user.type(
    screen.getByLabelText('11. What did you like most about the system, and what improvement would you suggest?'),
    'Clear shortlist.',
  )
  await user.click(screen.getByRole('button', { name: 'Submit evaluation' }))

  expect(await screen.findByText(/Your experience evaluation has been saved/)).toBeInTheDocument()
  expect(screen.getAllByText(/not an accuracy test/i).length).toBeGreaterThan(0)
  expect(fetchMock.mock.calls.some(([url, init]) => String(url).includes('experience-evaluation') && init?.method === 'POST')).toBe(
    true,
  )
})

test('shows a saved evaluation instead of asking again', async () => {
  stubEvaluation((url) => {
    if (url.includes(`/api/v1/recommendations/${RUN_ID}/experience-evaluation`)) {
      return jsonResponse(200, savedEvaluation)
    }
    return undefined
  })
  renderApp(`/recommendations/${RUN_ID}/evaluate`)
  expect(await screen.findByText(/Your experience evaluation has been saved/)).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Submit evaluation' })).not.toBeInTheDocument()
  expect(screen.getByDisplayValue('Clear explanations.')).toBeDisabled()
})
