import { screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import { jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'

afterEach(() => {
  restoreFetch()
})

test('authentication state is restored from the current-user endpoint', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    return undefined
  })

  renderApp('/')

  expect(await screen.findByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Log in' })).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Start Your Career Assessment' })).toHaveAttribute(
    'href',
    '/assessment',
  )
})
