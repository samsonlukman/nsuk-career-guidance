import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test } from 'vitest'

import { emptyDashboard, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'

beforeEach(() => {
  stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(401, { error: { code: 'unauthenticated', message: 'Authentication required' } })
    }
    if (url.includes('/api/v1/auth/login') && init?.method === 'POST') {
      return jsonResponse(200, studentUser)
    }
    if (url.includes('/api/v1/me/dashboard')) {
      return jsonResponse(200, emptyDashboard)
    }
    return undefined
  })
})

afterEach(() => {
  restoreFetch()
})

test('login form authenticates and opens the dashboard', async () => {
  const user = userEvent.setup()
  renderApp('/login')

  expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
  expect(screen.getByLabelText('Email address')).toBeInTheDocument()
  expect(screen.getByLabelText('Password')).toBeInTheDocument()

  await user.type(screen.getByLabelText('Email address'), 'amina@example.nsuk.test')
  await user.type(screen.getByLabelText('Password'), 'CorrectHorse9')
  await user.click(screen.getByRole('button', { name: 'Log in' }))

  expect(await screen.findByRole('heading', { name: 'Welcome, Amina Bello' })).toBeInTheDocument()
})
