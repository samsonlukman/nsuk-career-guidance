import { afterEach, expect, test, vi } from 'vitest'

import { apiRequest, ApiError } from './client'
import { jsonResponse, restoreFetch } from '../test/helpers'

afterEach(() => {
  restoreFetch()
})

test('API client surfaces structured backend errors', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      jsonResponse(422, {
        error: { code: 'invalid_faculty', message: 'Faculty must be one of the official NSUK faculties' },
      }),
    ),
  )

  const error = await apiRequest('/api/v1/me/profile', { method: 'PUT', body: '{}' }).catch((err: unknown) => err)
  expect(error).toBeInstanceOf(ApiError)
  expect(error).toMatchObject({
    status: 422,
    code: 'invalid_faculty',
    message: 'Faculty must be one of the official NSUK faculties',
  })
})

test('API client reports a network failure', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))),
  )

  const error = await apiRequest('/api/v1/auth/me').catch((err: unknown) => err)
  expect(error).toBeInstanceOf(ApiError)
  expect((error as ApiError).code).toBe('network_error')
})
