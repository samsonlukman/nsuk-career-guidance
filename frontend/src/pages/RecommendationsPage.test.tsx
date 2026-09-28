import { screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import { jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'
import { FLAG_ITEM_ID, mockRecommendationRun, RUN_ID, TOP_ITEM_ID } from '../test/recommendationFixture'

function stubRun(handler?: (url: string, init?: RequestInit) => Promise<Response> | Response | undefined) {
  return stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    const extra = handler?.(url, init)
    if (extra) return extra
    if (url.includes(`/api/v1/recommendations/${RUN_ID}`)) {
      return jsonResponse(200, mockRecommendationRun)
    }
    return undefined
  })
}

afterEach(() => {
  restoreFetch()
})

test('loads persisted recommendations in rank order', async () => {
  stubRun()
  renderApp(`/recommendations/${RUN_ID}`)

  expect(await screen.findByRole('heading', { name: 'Your Career Recommendations' })).toBeInTheDocument()
  expect(screen.getByText(/comparing your assessment profile/)).toBeInTheDocument()
  const titles = screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent)
  expect(titles[0]).toContain('Computer Science Teachers, Postsecondary')
  expect(titles[1]).toContain('Architecture Teachers, Postsecondary')
  expect(titles[2]).toContain('Dietitians and Nutritionists')
  expect(screen.getByText('Closest profile match')).toBeInTheDocument()
  expect(screen.getAllByText(/Profile similarity/)[0]).toBeInTheDocument()
  expect(screen.getByText('0.833')).toBeInTheDocument()
  expect(screen.queryByText(/87% chance/)).not.toBeInTheDocument()
  expect(screen.queryByText(/Weighted Block Cosine/)).not.toBeInTheDocument()
})

test('shows persisted explanations, contributions, zone 5, and flags', async () => {
  stubRun()
  renderApp(`/recommendations/${RUN_ID}`)
  await screen.findByRole('heading', { name: 'Your Career Recommendations' })

  expect(
    screen.getByText(/Computer Science Teachers, Postsecondary was recommended because your profile aligns on Professional Advising/),
  ).toBeInTheDocument()
  expect(screen.getAllByText(/Job Zone 5/)[0]).toBeInTheDocument()
  expect(screen.queryByText(/not recommended/i)).not.toBeInTheDocument()
  expect(screen.getByText('Additional education may be appropriate')).toBeInTheDocument()
  expect(screen.getByText('The occupation may differ from your preferred work setting')).toBeInTheDocument()
  expect(screen.getByText('Work setting mismatch: occupation has high public/customer contact')).toBeInTheDocument()
  expect(screen.queryByText('R-ZONE-5')).not.toBeInTheDocument()
  expect(screen.queryByText('R-CONTEXT')).not.toBeInTheDocument()
  expect(screen.getAllByRole('link', { name: 'View Career Details' })[0]).toHaveAttribute(
    'href',
    `/recommendations/${RUN_ID}/items/${TOP_ITEM_ID}`,
  )
})

test('shows a missing recommendation run', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) return jsonResponse(200, studentUser)
    if (url.includes('/api/v1/recommendations/')) {
      return jsonResponse(404, { error: { code: 'invalid_recommendation_run', message: 'Recommendation run was not found' } })
    }
    return undefined
  })
  renderApp(`/recommendations/${RUN_ID}`)
  expect(await screen.findByRole('alert')).toHaveTextContent('This recommendation run was not found.')
})

test('blocks unauthorized access to another student run', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) return jsonResponse(200, studentUser)
    if (url.includes('/api/v1/recommendations/')) {
      return jsonResponse(403, { error: { code: 'forbidden', message: 'Not allowed to access this recommendation run' } })
    }
    return undefined
  })
  renderApp(`/recommendations/${RUN_ID}`)
  expect(await screen.findByRole('alert')).toHaveTextContent('You cannot view another student\'s recommendation run.')
})

test('explains a session expiration and network failure', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) return jsonResponse(200, studentUser)
    if (url.includes('/api/v1/recommendations/')) {
      return jsonResponse(401, { error: { code: 'unauthenticated', message: 'Authentication required' } })
    }
    return undefined
  })
  renderApp(`/recommendations/${RUN_ID}`)
  expect(await screen.findByRole('alert')).toHaveTextContent('Your session has expired')
  expect(screen.getByRole('link', { name: 'Return to log in' })).toBeInTheDocument()
})

test('handles a malformed recommendation payload', async () => {
  stubRun((url) => {
    if (url.includes(`/api/v1/recommendations/${RUN_ID}`)) {
      return jsonResponse(200, { id: RUN_ID })
    }
    return undefined
  })
  renderApp(`/recommendations/${RUN_ID}`)
  expect(await screen.findByRole('alert')).toHaveTextContent('The recommendation data could not be displayed.')
})

test('renders recommendation cards in a list suitable for narrow screens', async () => {
  stubRun()
  renderApp(`/recommendations/${RUN_ID}`)
  await screen.findByRole('heading', { name: 'Your Career Recommendations' })
  expect(screen.getAllByRole('link', { name: 'View Career Details' })).toHaveLength(3)
  expect(document.querySelector('.recommendation-list')).not.toBeNull()
  expect(FLAG_ITEM_ID).toBeTruthy()
})
