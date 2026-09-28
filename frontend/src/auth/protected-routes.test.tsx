import { screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'

import { adminUser, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch, unauthenticatedFetch } from '../test/helpers'
import { mockAdminDashboard } from '../test/adminFixture'

afterEach(() => {
  restoreFetch()
})

test('unauthenticated visitors are sent from the dashboard to login', async () => {
  unauthenticatedFetch()
  renderApp('/dashboard')
  expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
})

test('students cannot open the admin route', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, studentUser)
    }
    if (url.includes('/api/v1/me/dashboard')) {
      return jsonResponse(200, {
        user: studentUser,
        has_completed_assessment: false,
        latest_assessment: null,
        latest_recommendation: null,
        recommendation_history: [],
      })
    }
    return undefined
  })
  renderApp('/admin')
  expect(await screen.findByRole('heading', { name: 'Welcome, Amina Bello' })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Admin dashboard' })).not.toBeInTheDocument()
})

test('administrators are sent from the student dashboard to admin', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, adminUser)
    }
    if (url.includes('/api/v1/admin/dashboard')) {
      return jsonResponse(200, mockAdminDashboard)
    }
    return undefined
  })
  renderApp('/dashboard')
  expect(await screen.findByRole('heading', { name: 'Admin dashboard' })).toBeInTheDocument()
})
