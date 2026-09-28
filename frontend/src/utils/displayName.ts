import type { CurrentUser } from '../types/auth'

export function displayName(user: CurrentUser): string {
  const first = user.profile.first_name?.trim()
  const last = user.profile.last_name?.trim()
  const full = [first, last].filter(Boolean).join(' ')
  return full || user.email
}

export function assessmentStatusLabel(hasCompleted: boolean, status: string | null | undefined): string {
  if (!status) {
    return 'No assessment yet'
  }
  if (hasCompleted || status === 'completed') {
    return 'Assessment completed'
  }
  if (status === 'in_progress') {
    return 'Assessment in progress'
  }
  return `Assessment ${status.replaceAll('_', ' ')}`
}
