import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import {
  mockAdminDashboard,
  mockAdminRunDetail,
  mockAuditList,
  mockCatalog,
  mockConfig,
  mockOnetSnapshot,
  mockPrior,
  mockPriorList,
  mockQuestionnaire,
  mockRatingList,
  mockRunList,
  mockStudentDetail,
  mockStudentList,
} from '../../test/adminFixture'
import { adminUser, jsonResponse, renderApp, restoreFetch, studentUser, stubFetch } from '../../test/helpers'
import { RUN_ID } from '../../test/recommendationFixture'

function stubAdmin(handler?: (url: string, init?: RequestInit) => Promise<Response> | Response | undefined) {
  return stubFetch((url, init) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(200, adminUser)
    }
    const extra = handler?.(url, init)
    if (extra) return extra
    if (url.includes('/api/v1/admin/dashboard')) return jsonResponse(200, mockAdminDashboard)
    if (url.includes('/api/v1/admin/students/') && !url.endsWith('/students')) {
      return jsonResponse(200, mockStudentDetail)
    }
    if (url.includes('/api/v1/admin/students')) return jsonResponse(200, mockStudentList)
    if (url.includes(`/api/v1/admin/recommendation-runs/${RUN_ID}`)) {
      return jsonResponse(200, mockAdminRunDetail)
    }
    if (url.includes('/api/v1/admin/recommendation-runs')) return jsonResponse(200, mockRunList)
    if (url.includes('/api/v1/admin/ratings')) return jsonResponse(200, mockRatingList)
    if (url.includes('/api/v1/admin/onet-snapshot')) return jsonResponse(200, mockOnetSnapshot)
    if (url.includes('/api/v1/admin/questionnaire')) return jsonResponse(200, mockQuestionnaire)
    if (url.includes('/api/v1/admin/recommendation-config')) return jsonResponse(200, mockConfig)
    if (url.includes('/faculty-knowledge-priors/catalog')) return jsonResponse(200, mockCatalog)
    if (url.includes('/faculty-knowledge-priors/audits')) return jsonResponse(200, mockAuditList)
    if (url.includes('/faculty-knowledge-priors')) return jsonResponse(200, mockPriorList())
    return undefined
  })
}

afterEach(() => {
  restoreFetch()
})

test('students cannot open the admin dashboard route', async () => {
  stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) return jsonResponse(200, studentUser)
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

test('renders stored admin dashboard statistics', async () => {
  stubAdmin()
  renderApp('/admin')
  expect(await screen.findByRole('heading', { name: 'Admin dashboard' })).toBeInTheDocument()
  expect(screen.getByText('Registered students')).toBeInTheDocument()
  expect(screen.getByText('12')).toBeInTheDocument()
  expect(screen.getByText('Completed assessments')).toBeInTheDocument()
  expect(screen.getByText('4')).toBeInTheDocument()
  expect(screen.getByText(/questionnaire_v1/)).toBeInTheDocument()
  expect(screen.getByText(/config_v1/)).toBeInTheDocument()
  expect(screen.getAllByText(/30\.3/).length).toBeGreaterThan(0)
  expect(screen.getByText('connected')).toBeInTheDocument()
  expect(screen.getAllByText(/not a measure of recommendation accuracy/i).length).toBeGreaterThan(0)
})

test('shows an API error on the admin dashboard', async () => {
  stubAdmin((url) => {
    if (url.includes('/api/v1/admin/dashboard')) {
      return jsonResponse(500, { error: { code: 'internal_error', message: 'An unexpected error occurred' } })
    }
    return undefined
  })
  renderApp('/admin')
  expect(await screen.findByRole('alert')).toHaveTextContent('An unexpected error occurred')
})

test('lists stored students and opens a student record', async () => {
  stubAdmin()
  renderApp('/admin/students')
  expect(await screen.findByRole('heading', { name: 'Students' })).toBeInTheDocument()
  expect(screen.getByText(studentUser.email)).toBeInTheDocument()
  expect(screen.getByText('Natural and Applied Sciences')).toBeInTheDocument()
  expect(screen.queryByText(/password_hash/i)).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('link', { name: 'Amina Bello' }))
  expect(await screen.findByRole('heading', { name: 'Amina Bello' })).toBeInTheDocument()
  expect(screen.getByText('NSU/2021/001')).toBeInTheDocument()
  expect(screen.getByText('completed')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Computer Science Teachers, Postsecondary' })).toHaveAttribute(
    'href',
    `/admin/recommendations/${RUN_ID}`,
  )
})

test('lists recommendation activity from persisted runs', async () => {
  stubAdmin()
  renderApp('/admin/recommendations')
  expect(await screen.findByRole('heading', { name: 'Recommendation activity' })).toBeInTheDocument()
  expect(screen.getByText('Amina Bello')).toBeInTheDocument()
  expect(screen.getByText('questionnaire_v1 · config_v1 · 30.3')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Computer Science Teachers, Postsecondary' })).toHaveAttribute(
    'href',
    `/admin/recommendations/${RUN_ID}`,
  )
})

test('inspects a persisted recommendation run without inventing scores', async () => {
  stubAdmin()
  renderApp(`/admin/recommendations/${RUN_ID}`)
  expect(await screen.findByRole('heading', { name: 'Inspect recommendation run' })).toBeInTheDocument()
  expect(screen.getByText(/amina@example.nsuk.test/i)).toBeInTheDocument()
  expect(screen.getAllByText(/Dietitians and Nutritionists/).length).toBeGreaterThan(0)
  expect(screen.getAllByText(/Why this was recommended/).length).toBeGreaterThan(0)
  expect(screen.getAllByText(/Profile similarity/i).length).toBeGreaterThan(0)
  expect(screen.queryByText(/87% chance/i)).not.toBeInTheDocument()
})

test('shows relevance feedback without calling it accuracy', async () => {
  stubAdmin()
  renderApp('/admin/feedback')
  expect(await screen.findByRole('heading', { name: 'Recommendation feedback' })).toBeInTheDocument()
  expect(screen.getAllByText('4 of 5').length).toBeGreaterThan(0)
  expect(screen.getByText('Useful as a discussion prompt')).toBeInTheDocument()
  expect(screen.getAllByText(/not a measure of recommendation accuracy/i).length).toBeGreaterThan(0)
  expect(screen.queryByText(/AI accuracy/i)).not.toBeInTheDocument()
})

test('shows the active O*NET snapshot as read-only', async () => {
  stubAdmin()
  renderApp('/admin/onet')
  expect(await screen.findByRole('heading', { name: 'Active O*NET snapshot' })).toBeInTheDocument()
  expect(screen.getByText('30.3')).toBeInTheDocument()
  expect(screen.getByText('923')).toBeInTheDocument()
  expect(screen.getByText('Job Zone Five: Extensive Preparation Needed')).toBeInTheDocument()
  expect(screen.getAllByText(/read-only/i).length).toBeGreaterThan(0)
})

test('shows the active questionnaire for inspection', async () => {
  stubAdmin()
  renderApp('/admin/questionnaire')
  expect(await screen.findByRole('heading', { name: 'Active questionnaire' })).toBeInTheDocument()
  expect(screen.getByText('questionnaire_v1')).toBeInTheDocument()
  expect(screen.getByText(/Select knowledge areas/)).toBeInTheDocument()
  expect(screen.getByText(/Editing is not available/)).toBeInTheDocument()
})

test('shows recommendation configuration without edit controls', async () => {
  stubAdmin()
  renderApp('/admin/configuration')
  expect(await screen.findByRole('heading', { name: 'Active configuration' })).toBeInTheDocument()
  expect(screen.getByText('config_v1')).toBeInTheDocument()
  expect(screen.getByText('weighted_block_cosine')).toBeInTheDocument()
  expect(screen.getByText('riasec')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /save|edit|change/i })).not.toBeInTheDocument()
})

test('adds a faculty knowledge mapping from official catalog values', async () => {
  let created: unknown
  stubAdmin((url, init) => {
    if (url.endsWith('/faculty-knowledge-priors') && init?.method === 'POST') {
      created = init.body ? JSON.parse(String(init.body)) : null
      return jsonResponse(201, mockPrior)
    }
    if (url.endsWith('/faculty-knowledge-priors') && init?.method !== 'POST') {
      return jsonResponse(200, created ? mockPriorList([mockPrior]) : mockPriorList())
    }
    return undefined
  })
  renderApp('/admin/faculty-priors')
  expect(await screen.findByRole('heading', { name: 'Faculty → knowledge priors' })).toBeInTheDocument()
  const user = userEvent.setup()
  await user.selectOptions(screen.getByLabelText('Faculty'), 'Natural and Applied Sciences')
  await user.selectOptions(screen.getByLabelText('O*NET knowledge element'), '2.C.3.a')
  await user.click(screen.getByRole('button', { name: 'Add mapping' }))
  expect(created).toEqual({
    faculty: 'Natural and Applied Sciences',
    element_id: '2.C.3.a',
  })
  expect(await screen.findByText('Computers and Electronics')).toBeInTheDocument()
  expect(screen.getByText('Mapping added. Future recommendation runs will use the updated faculty knowledge prior.')).toBeInTheDocument()
})

test('shows a faculty-prior API error', async () => {
  stubAdmin((url, init) => {
    if (url.endsWith('/faculty-knowledge-priors') && init?.method === 'POST') {
      return jsonResponse(422, {
        error: { code: 'invalid_faculty', message: 'Faculty is not an official NSUK faculty' },
      })
    }
    return undefined
  })
  renderApp('/admin/faculty-priors')
  const user = userEvent.setup()
  await screen.findByRole('heading', { name: 'Faculty → knowledge priors' })
  await user.click(screen.getByRole('button', { name: 'Add mapping' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Faculty is not an official NSUK faculty')
})
