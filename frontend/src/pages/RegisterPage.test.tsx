import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test } from 'vitest'

import { emptyDashboard, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'

beforeEach(() => {
  stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(401, { error: { code: 'unauthenticated', message: 'Authentication required' } })
    }
    if (url.includes('/api/v1/auth/register') && init?.method === 'POST') {
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

test('registration form has labelled fields and creates an account', async () => {
  const user = userEvent.setup()
  renderApp('/register')

  expect(await screen.findByRole('heading', { name: 'Register' })).toBeInTheDocument()
  expect(screen.getByLabelText('First name')).toBeInTheDocument()
  expect(screen.getByLabelText('Last name')).toBeInTheDocument()
  expect(screen.getByLabelText('Matriculation number')).toBeInTheDocument()
  expect(screen.getByLabelText('Email address')).toBeInTheDocument()
  expect(screen.getByLabelText('Password')).toBeInTheDocument()

  await user.type(screen.getByLabelText('First name'), 'Amina')
  await user.type(screen.getByLabelText('Last name'), 'Bello')
  await user.type(screen.getByLabelText('Email address'), 'amina@example.nsuk.test')
  await user.type(screen.getByLabelText('Password'), 'CorrectHorse9')
  await user.click(screen.getByRole('button', { name: 'Create account' }))

  expect(await screen.findByRole('heading', { name: 'Welcome, Amina Bello' })).toBeInTheDocument()
  expect(globalThis.fetch).toHaveBeenCalledWith(
    '/api/v1/auth/register',
    expect.objectContaining({
      method: 'POST',
      credentials: 'include',
    }),
  )
})
