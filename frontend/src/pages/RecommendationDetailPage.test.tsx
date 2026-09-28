import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test } from 'vitest'

import { jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'
import {
  FLAG_ITEM_ID,
  MID_ITEM_ID,
  mockOccupation,
  mockRating,
  mockRecommendationRun,
  RUN_ID,
  TOP_ITEM_ID,
} from '../test/recommendationFixture'

function stubDetail(handler?: (url: string, init?: RequestInit) => Promise<Response> | Response | undefined) {
  return stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    const extra = handler?.(url, init)
    if (extra) return extra
    if (url.includes(`/api/v1/recommendations/${RUN_ID}`)) {
      return jsonResponse(200, mockRecommendationRun)
    }
    if (url.includes('/api/v1/occupations/25-1021.00')) {
      return jsonResponse(200, mockOccupation)
    }
    return undefined
  })
}

afterEach(() => {
  restoreFetch()
})

test('opens occupation details from the stored recommendation', async () => {
  stubDetail()
  renderApp(`/recommendations/${RUN_ID}/items/${TOP_ITEM_ID}`)

  expect(await screen.findByRole('heading', { name: 'Computer Science Teachers, Postsecondary' })).toBeInTheDocument()
  expect(await screen.findByText(/Teach courses in computer science/)).toBeInTheDocument()
  expect(screen.getByText(/Why this was recommended/)).toBeInTheDocument()
  expect(screen.getByText(/Professional Advising and related O\*NET features/)).toBeInTheDocument()
  expect(screen.getByText('Specific Interests')).toBeInTheDocument()
  expect(screen.getByText('Knowledge')).toBeInTheDocument()
  expect(screen.getByText('Skills')).toBeInTheDocument()
  expect(screen.getAllByText('Selected area is also important in this occupation').length).toBeGreaterThan(0)
  expect(screen.getByText(/Job Zone Five: Extensive Preparation Needed/)).toBeInTheDocument()
  expect(screen.getByText(/Master's Degree/)).toBeInTheDocument()
  expect(screen.queryByText(/salary/i)).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Next: Architecture Teachers/ })).toHaveAttribute(
    'href',
    `/recommendations/${RUN_ID}/items/${MID_ITEM_ID}`,
  )
})

test('shows zone 5 information without calling the occupation not recommended', async () => {
  stubDetail((url) => {
    if (url.includes('/api/v1/occupations/29-1031.00')) {
      return jsonResponse(200, {
        ...mockOccupation,
        onetsoc_code: '29-1031.00',
        title: 'Dietitians and Nutritionists',
        description: 'Plan and conduct food service or nutritional programs.',
      })
    }
    return undefined
  })
  renderApp(`/recommendations/${RUN_ID}/items/${FLAG_ITEM_ID}`)
  expect(await screen.findByText('Additional education may be appropriate')).toBeInTheDocument()
  expect(screen.getByText('Job Zone 5 typically requires graduate or professional training')).toBeInTheDocument()
  expect(screen.queryByText(/not recommended/i)).not.toBeInTheDocument()
  expect(screen.getByText('The occupation may differ from your preferred work setting')).toBeInTheDocument()
})

test('requires a rating before submission and then saves feedback', async () => {
  let body: unknown
  stubDetail((url, init) => {
    if (url.includes(`/api/v1/recommendations/${TOP_ITEM_ID}/rating`) && init?.method === 'POST') {
      body = init.body ? JSON.parse(String(init.body)) : null
      return jsonResponse(200, mockRating)
    }
    return undefined
  })
  const user = userEvent.setup()
  renderApp(`/recommendations/${RUN_ID}/items/${TOP_ITEM_ID}`)
  await screen.findByRole('heading', { name: 'Your feedback' })
  await user.click(screen.getByRole('button', { name: 'Save feedback' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Choose a relevance rating from 1 to 5.')
  await user.click(screen.getByLabelText('4'))
  await user.click(screen.getByRole('button', { name: 'Save feedback' }))
  expect(await screen.findByRole('status')).toHaveTextContent('user relevance feedback')
  expect(body).toEqual({ relevance_1_to_5: 4, comment: null })
})

test('prevents a second rating request while the first is in flight', async () => {
  let resolveRating: ((value: Response) => void) | undefined
  stubDetail((url, init) => {
    if (url.includes('/rating') && init?.method === 'POST') {
      return new Promise((resolve) => {
        resolveRating = resolve
      })
    }
    return undefined
  })
  const user = userEvent.setup()
  renderApp(`/recommendations/${RUN_ID}/items/${TOP_ITEM_ID}`)
  await screen.findByRole('heading', { name: 'Your feedback' })
  await user.click(screen.getByLabelText('5'))
  await user.click(screen.getByRole('button', { name: 'Save feedback' }))
  expect(await screen.findByRole('button', { name: 'Saving feedback…' })).toBeDisabled()
  resolveRating?.(await jsonResponse(200, mockRating))
  expect(await screen.findByRole('status')).toHaveTextContent('user relevance feedback')
})
