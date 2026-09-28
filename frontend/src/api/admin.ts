import { apiRequest } from './client'
import type {
  AdminDashboard,
  AdminHealth,
  AdminOnetSnapshot,
  AdminQuestionnaire,
  AdminRatingList,
  AdminRecommendationConfig,
  AdminRunDetail,
  AdminRunList,
  AdminStudentDetail,
  AdminStudentList,
  FacultyKnowledgeCatalog,
  FacultyKnowledgePrior,
  FacultyKnowledgePriorAuditList,
  FacultyKnowledgePriorList,
  FacultyKnowledgePriorWrite,
} from '../types/admin'

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  }
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

export function fetchAdminDashboard() {
  return apiRequest<AdminDashboard>('/api/v1/admin/dashboard')
}

export function fetchAdminHealth() {
  return apiRequest<AdminHealth>('/api/v1/admin/health')
}

export function fetchAdminStudents(params: { q?: string; page?: number; page_size?: number } = {}) {
  return apiRequest<AdminStudentList>(`/api/v1/admin/students${query(params)}`)
}

export function fetchAdminStudent(studentId: string) {
  return apiRequest<AdminStudentDetail>(`/api/v1/admin/students/${studentId}`)
}

export function fetchAdminRuns(params: { page?: number; page_size?: number } = {}) {
  return apiRequest<AdminRunList>(`/api/v1/admin/recommendation-runs${query(params)}`)
}

export function fetchAdminRun(runId: string) {
  return apiRequest<AdminRunDetail>(`/api/v1/admin/recommendation-runs/${runId}`)
}

export function fetchAdminRatings(params: { page?: number; page_size?: number } = {}) {
  return apiRequest<AdminRatingList>(`/api/v1/admin/ratings${query(params)}`)
}

export function fetchAdminOnetSnapshot() {
  return apiRequest<AdminOnetSnapshot>('/api/v1/admin/onet-snapshot')
}

export function fetchAdminQuestionnaire() {
  return apiRequest<AdminQuestionnaire>('/api/v1/admin/questionnaire')
}

export function fetchAdminRecommendationConfig() {
  return apiRequest<AdminRecommendationConfig>('/api/v1/admin/recommendation-config')
}

export function fetchFacultyPriorCatalog() {
  return apiRequest<FacultyKnowledgeCatalog>('/api/v1/admin/faculty-knowledge-priors/catalog')
}

export function fetchFacultyPriors() {
  return apiRequest<FacultyKnowledgePriorList>('/api/v1/admin/faculty-knowledge-priors')
}

export function fetchFacultyPriorAudits(params: { page?: number; page_size?: number } = {}) {
  return apiRequest<FacultyKnowledgePriorAuditList>(`/api/v1/admin/faculty-knowledge-priors/audits${query(params)}`)
}

export function createFacultyPrior(payload: FacultyKnowledgePriorWrite) {
  return apiRequest<FacultyKnowledgePrior>('/api/v1/admin/faculty-knowledge-priors', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateFacultyPrior(priorId: number, payload: FacultyKnowledgePriorWrite) {
  return apiRequest<FacultyKnowledgePrior>(`/api/v1/admin/faculty-knowledge-priors/${priorId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteFacultyPrior(priorId: number) {
  return apiRequest<null>(`/api/v1/admin/faculty-knowledge-priors/${priorId}`, {
    method: 'DELETE',
  })
}
