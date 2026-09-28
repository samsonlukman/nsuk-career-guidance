import { screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import { emptyDashboard, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../test/helpers'
import { dashboardWithRun, RUN_ID } from '../test/recommendationFixture'

afterEach(() => {
  restoreFetch()
})

test('dashboard shows welcome text and an empty assessment state', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    if (url.includes('/api/v1/me/dashboard')) {
      return jsonResponse(200, emptyDashboard)
    }
    return undefined
  })

  renderApp('/dashboard')

  expect(await screen.findByRole('heading', { name: 'Welcome, Amina Bello' })).toBeInTheDocument()
  expect(screen.getByText('No assessment yet')).toBeInTheDocument()
  expect(screen.getByText('You have not started an assessment')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Start your career assessment' })).toBeInTheDocument()
  expect(screen.getByText('No recommendation run yet')).toBeInTheDocument()
  expect(screen.getByText('There is no stored recommendation history for this account.')).toBeInTheDocument()
  expect(screen.queryByText('Software Developers')).not.toBeInTheDocument()
})

test('links the latest stored recommendation run to the results page', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    if (url.includes('/api/v1/me/dashboard')) {
      return jsonResponse(200, dashboardWithRun)
    }
    return undefined
  })

  renderApp('/dashboard')

  expect(await screen.findByText('Computer Science Teachers, Postsecondary (25-1021.00)')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'View Recommendations' })).toHaveAttribute(
    'href',
    `/recommendations/${RUN_ID}`,
  )
  expect(screen.getByRole('link', { name: 'View' })).toHaveAttribute('href', `/recommendations/${RUN_ID}`)
})
