import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test } from 'vitest'

import { emptyDashboard, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'

afterEach(() => {
  restoreFetch()
})

test('logout clears the session and returns to the public site', async () => {
  let signedIn = true
  stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/logout') && init?.method === 'POST') {
      signedIn = false
      return jsonResponse(200, { status: 'ok' })
    }
    if (url.includes('/api/v1/auth/me')) {
      return signedIn
        ? jsonResponse(200, studentUser)
        : jsonResponse(401, { error: { code: 'unauthenticated', message: 'Authentication required' } })
    }
    if (url.includes('/api/v1/me/dashboard')) {
      return jsonResponse(200, emptyDashboard)
    }
    return undefined
  })

  const user = userEvent.setup()
  renderApp('/dashboard')
  expect(await screen.findByRole('heading', { name: 'Welcome, Amina Bello' })).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Log out' }))

  expect(
    await screen.findByRole('heading', {
      name: /AI-Powered Personalized Career Guidance for NSUK Students/i,
    }),
  ).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Log in' })).toBeInTheDocument()
})
