import { render, type RenderResult } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

import { AppRoutes } from '../App'
import { AuthProvider } from '../auth/AuthContext'
import type { CurrentUser } from '../types/auth'
import type { Dashboard } from '../types/api'

export const adminUser: CurrentUser = {
  id: '22222222-2222-2222-2222-222222222222',
  email: 'admin@example.nsuk.test',
  role: 'admin',
  is_active: true,
  profile: {
    first_name: 'Ada',
    last_name: 'Okeke',
    matric_number: null,
    faculty: null,
    department: null,
    level: null,
    further_study: null,
    course_relatedness: null,
  },
}

export const studentUser: CurrentUser = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'amina@example.nsuk.test',
  role: 'student',
  is_active: true,
  profile: {
    first_name: 'Amina',
    last_name: 'Bello',
    matric_number: 'NSU/2021/001',
    faculty: null,
    department: null,
    level: null,
    further_study: null,
    course_relatedness: null,
  },
}

export const emptyDashboard: Dashboard = {
  user: studentUser,
  has_completed_assessment: false,
  latest_assessment: null,
  latest_recommendation: null,
  recommendation_history: [],
}

export function jsonResponse(status: number, body: unknown): Promise<Response> {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    text: async () => (body === undefined ? '' : JSON.stringify(body)),
  } as Response)
}

type Handler = (url: string, init?: RequestInit) => Promise<Response> | Response | undefined

export function stubFetch(handler: Handler) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
    const result = await handler(url, init)
    if (result) return result
    return jsonResponse(404, { error: { code: 'not_found', message: `No mock for ${url}` } })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export function restoreFetch() {
  const current = globalThis.fetch
  if (typeof current === 'function' && 'mockReset' in current) {
    ;(current as ReturnType<typeof vi.fn>).mockReset()
  }
}

export function unauthenticatedFetch() {
  return stubFetch((url) => {
    if (url.includes('/api/v1/auth/me')) {
      return jsonResponse(401, { error: { code: 'unauthenticated', message: 'Authentication required' } })
    }
    return undefined
  })
}

export function renderApp(path = '/'): RenderResult {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </MemoryRouter>,
  )
}
