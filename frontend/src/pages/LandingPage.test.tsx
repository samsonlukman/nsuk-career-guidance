import { screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test } from 'vitest'

import { renderApp, restoreFetch, unauthenticatedFetch } from '../test/helpers'

beforeEach(() => {
  unauthenticatedFetch()
})

afterEach(() => {
  restoreFetch()
})

test('landing page explains the system and uses the primary CTA', async () => {
  renderApp('/')

  expect(
    await screen.findByRole('heading', {
      name: /AI-Powered Personalized Career Guidance for NSUK Students/i,
    }),
  ).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Start Your Career Assessment' })).toHaveAttribute('href', '/register')
  expect(screen.getByText(/undergraduate students of Nasarawa State University, Keffi/i)).toBeInTheDocument()
  expect(screen.getByText(/does not replace counsellors/i)).toBeInTheDocument()
  expect(document.body.textContent ?? '').not.toMatch(/O\*NET/i)
  expect(document.body.textContent ?? '').not.toMatch(/k-nearest/i)
  expect(document.body.textContent ?? '').not.toMatch(/\bAPI\b/)

  const text = document.body.textContent ?? ''
  expect(text.toLowerCase()).not.toMatch(/guaranteed employment/)
  expect(text.toLowerCase()).not.toMatch(/guaranteed career success/)
  expect(text.toLowerCase()).not.toMatch(/proven accuracy/)
  expect(text.toLowerCase()).not.toMatch(/replaces professional/)
})
