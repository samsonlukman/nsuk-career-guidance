import { screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import { emptyDashboard, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'

afterEach(() => {
  restoreFetch()
})

test('protected pages show a session loading state', () => {
  stubFetch(() => new Promise(() => undefined))
  renderApp('/dashboard')
  expect(screen.getByRole('status')).toHaveTextContent('Checking your session')
})

test('dashboard shows a loading state while data is fetched', async () => {
  const resolvers: Array<(value: Response) => void> = []
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    if (url.includes('/api/v1/me/dashboard')) {
      return new Promise((resolve) => {
        resolvers.push(resolve)
      })
    }
    return undefined
  })

  renderApp('/dashboard')
  expect(await screen.findByText('Loading your dashboard…')).toBeInTheDocument()

  const payload = await jsonResponse(200, emptyDashboard)
  resolvers.forEach((resolve) => resolve(payload))
  expect(await screen.findByRole('heading', { name: 'Welcome, Amina Bello' })).toBeInTheDocument()
})
