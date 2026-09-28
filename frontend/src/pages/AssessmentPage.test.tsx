import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test } from 'vitest'

import { saveAssessmentDraft } from '../utils/assessmentAnswers'
import { jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'
import { mockQuestionnaire, mockSubmitConfirmation } from '../test/questionnaireFixture'

function stubQuestionnaire(handler?: (url: string, init?: RequestInit) => Promise<Response> | Response | undefined) {
  return stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    const extra = handler?.(url, init)
    if (extra) return extra
    if (url.includes('/api/v1/questionnaires/active')) {
      return jsonResponse(200, mockQuestionnaire)
    }
    return undefined
  })
}

async function continueRequiredChoice(user: ReturnType<typeof userEvent.setup>, name: string) {
  await user.click(screen.getByLabelText(name))
  await user.click(screen.getByRole('button', { name: 'Continue' }))
}

const completeAnswers = {
  level: { kind: 'value' as const, value: '200' },
  interest_realistic: { kind: 'value' as const, value: '5' },
  sia: { kind: 'selections' as const, selections: [{ element_id: '1.B.3.b', value: 6 }] },
  knowledge: { kind: 'selections' as const, selections: [{ element_id: '2.C.3.a', value: 4 }] },
  pref_indoor: { kind: 'value' as const, value: '3' },
}

function seedReviewDraft() {
  saveAssessmentDraft(studentUser.id, {
    questionnaireVersion: 'questionnaire_v1',
    stepIndex: 6,
    answers: completeAnswers,
    updatedAt: '2026-08-24T00:00:00.000Z',
  })
}

function seedSparseDraft(stepIndex: number) {
  saveAssessmentDraft(studentUser.id, {
    questionnaireVersion: 'questionnaire_v1',
    stepIndex,
    answers: {
      level: { kind: 'value', value: '200' },
      interest_realistic: { kind: 'value', value: '4' },
    },
    updatedAt: '2026-08-24T00:00:00.000Z',
  })
}

afterEach(() => {
  restoreFetch()
})

test('loads the questionnaire from the API and shows progress', async () => {
  stubQuestionnaire()
  renderApp('/assessment')

  expect(await screen.findByText('What is your current undergraduate level?')).toBeInTheDocument()
  expect(screen.getByText(/Section 1 of 5/)).toBeInTheDocument()
  expect(screen.getByText('Question 1 of 2 in this section')).toBeInTheDocument()
  expect(screen.getByText('Question 1 of 6')).toBeInTheDocument()
  expect(screen.getByRole('progressbar', { name: 'Assessment progress' })).toBeInTheDocument()
})

test('blocks continue when a required field is empty', async () => {
  stubQuestionnaire()
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByText('What is your current undergraduate level?')
  await user.click(screen.getByRole('button', { name: 'Continue' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('This question is required.')
})

test('navigates between sections and keeps answers when going back', async () => {
  stubQuestionnaire()
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByText('What is your current undergraduate level?')
  await continueRequiredChoice(user, '300 level')
  expect(await screen.findByLabelText(/Department \/ programme/)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Back' }))
  expect(screen.getByLabelText('300 level')).toBeChecked()
})

test('prevents selecting more SIA areas than the API maximum', async () => {
  stubQuestionnaire()
  seedSparseDraft(3)
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByRole('heading', { name: 'Specific Interest Areas' })

  for (const label of ['Mechanics', 'Computers', 'Visual Arts', 'Teaching', 'Sales']) {
    await user.click(screen.getByLabelText(label))
  }
  const extra = screen.getByRole('checkbox', { name: /Accounting/ })
  expect(extra).toBeDisabled()
  await user.click(extra)
  expect(extra).not.toBeChecked()
  expect(screen.getByText('5 selected (maximum 5)')).toBeInTheDocument()
})

test('prevents selecting more knowledge areas than the API maximum', async () => {
  stubQuestionnaire()
  seedSparseDraft(4)
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByRole('heading', { name: 'Knowledge' })

  for (const label of ['Administration', 'Computers and Electronics', 'Mathematics', 'Physics', 'Psychology']) {
    await user.click(screen.getByLabelText(label))
  }
  expect(screen.getByRole('checkbox', { name: /English Language/ })).toBeDisabled()
})

test('requires a rating after a sparse selection', async () => {
  stubQuestionnaire()
  seedSparseDraft(3)
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByRole('heading', { name: 'Specific Interest Areas' })
  await user.click(screen.getByLabelText('Teaching'))
  await user.click(screen.getByRole('button', { name: 'Continue' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Rate every selected area before continuing.')
})

test('rates selected SIA areas on the API scale, not the area list', async () => {
  stubQuestionnaire()
  seedSparseDraft(3)
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByRole('heading', { name: 'Specific Interest Areas' })
  await user.click(screen.getByLabelText('Teaching'))
  expect(screen.getByRole('radio', { name: /1/ })).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: /7/ })).toBeInTheDocument()
  expect(screen.queryByRole('radio', { name: /Mechanics/ })).not.toBeInTheDocument()
  await user.click(screen.getByRole('radio', { name: /6/ }))
  await user.click(screen.getByRole('button', { name: 'Continue' }))
  expect(await screen.findByRole('heading', { name: 'Knowledge' })).toBeInTheDocument()
})

test('recovers in-progress answers from local storage', async () => {
  saveAssessmentDraft(studentUser.id, {
    questionnaireVersion: 'questionnaire_v1',
    stepIndex: 2,
    answers: { level: { kind: 'value', value: '100' } },
    updatedAt: '2026-08-24T00:00:00.000Z',
  })
  stubQuestionnaire()
  renderApp('/assessment')
  expect(await screen.findByRole('heading', { name: 'RIASEC' })).toBeInTheDocument()
  expect(screen.getByText('How much would you enjoy realistic work?')).toBeInTheDocument()
})

test('shows the review screen and submits once', async () => {
  let posts = 0
  stubQuestionnaire((url, init) => {
    if (url.includes('/api/v1/assessments') && init?.method === 'POST') {
      posts += 1
      return jsonResponse(200, mockSubmitConfirmation)
    }
    return undefined
  })
  seedReviewDraft()
  const user = userEvent.setup()
  renderApp('/assessment')
  expect(await screen.findByRole('heading', { name: 'Review and submit' })).toBeInTheDocument()
  expect(screen.getByText('questionnaire_v1')).toBeInTheDocument()
  expect(screen.getByText(/Computers — 6/)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Submit Assessment' }))
  expect(await screen.findByRole('heading', { name: /Your answers were sent/ })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'View My Career Recommendations' })).toHaveAttribute(
    'href',
    `/recommendations/${mockSubmitConfirmation.id}`,
  )
  expect(posts).toBe(1)
})

test('prevents a second submit while the first request is in flight', async () => {
  let resolveSubmit: ((value: Response) => void) | undefined
  stubQuestionnaire((url, init) => {
    if (url.includes('/api/v1/assessments') && init?.method === 'POST') {
      return new Promise((resolve) => {
        resolveSubmit = resolve
      })
    }
    return undefined
  })
  seedReviewDraft()
  const user = userEvent.setup()
  renderApp('/assessment')
  await screen.findByRole('button', { name: 'Submit Assessment' })
  await user.click(screen.getByRole('button', { name: 'Submit Assessment' }))
  expect(await screen.findByRole('button', { name: 'Submitting assessment…' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: 'Submitting assessment…' }))
  resolveSubmit?.(await jsonResponse(200, mockSubmitConfirmation))
  await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(3))
  // auth/me + questionnaire + one POST
  const posts = (globalThis.fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls.filter((call) => {
    const init = call[1] as RequestInit | undefined
    return init?.method === 'POST'
  })
  expect(posts).toHaveLength(1)
})

test('keeps answers when submission fails', async () => {
  stubQuestionnaire((url, init) => {
    if (url.includes('/api/v1/assessments') && init?.method === 'POST') {
      return jsonResponse(500, { error: { code: 'internal_error', message: 'An unexpected error occurred' } })
    }
    return undefined
  })
  seedReviewDraft()
  const user = userEvent.setup()
  renderApp('/assessment')
  await user.click(await screen.findByRole('button', { name: 'Submit Assessment' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(/still saved on this device/)
  expect(screen.getByText(/Computers — 6/)).toBeInTheDocument()
})

test('explains session expiration without dropping the draft', async () => {
  stubQuestionnaire((url, init) => {
    if (url.includes('/api/v1/assessments') && init?.method === 'POST') {
      return jsonResponse(401, { error: { code: 'unauthenticated', message: 'Authentication required' } })
    }
    return undefined
  })
  seedReviewDraft()
  const user = userEvent.setup()
  renderApp('/assessment')
  await user.click(await screen.findByRole('button', { name: 'Submit Assessment' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Your session has expired')
  expect(screen.getByRole('link', { name: 'Return to log in' })).toBeInTheDocument()
})

test('shows a questionnaire load failure', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) return jsonResponse(200, studentUser)
    if (url.includes('/api/v1/questionnaires/active')) {
      return jsonResponse(500, { error: { code: 'internal_error', message: 'An unexpected error occurred' } })
    }
    return undefined
  })
  renderApp('/assessment')
  expect(await screen.findByRole('alert')).toHaveTextContent('An unexpected error occurred')
  expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
})
