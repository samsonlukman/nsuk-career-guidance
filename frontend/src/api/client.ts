import type { ApiErrorBody } from '../types/api'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details?: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

function toApiError(status: number, body: unknown): ApiError {
  if (body && typeof body === 'object' && 'error' in body) {
    const payload = body as ApiErrorBody
    return new ApiError(
      status,
      payload.error.code || 'http_error',
      payload.error.message || 'Request failed',
      payload.error.details,
    )
  }
  return new ApiError(status, 'http_error', 'Request failed')
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const hasBody = init.body !== undefined && init.body !== null
  if (hasBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers,
      credentials: 'include',
    })
  } catch {
    throw new ApiError(0, 'network_error', 'Unable to reach the server. Check your connection and try again.')
  }

  const body = await parseBody(response)
  if (!response.ok) {
    throw toApiError(response.status, body)
  }
  return body as T
}

export function getApiBaseUrl(): string {
  return BASE_URL
}
