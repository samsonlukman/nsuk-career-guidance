import type { ApiError } from '../api/client'
import type {
  FeatureContribution,
  RecommendationItem,
  RecommendationRun,
  RuleFlag,
} from '../types/recommendations'

export const BLOCK_LABELS: Record<string, string> = {
  riasec: 'Interests',
  sia: 'Specific Interests',
  essential_skills: 'Skills',
  transferable_skills: 'Transferable Skills',
  work_styles: 'Work Styles',
  knowledge: 'Knowledge',
}

const FLAG_HEADINGS: Record<string, string> = {
  'R-ZONE-5': 'Additional education may be appropriate',
  'R-EDU': 'Further education may be required',
  'R-CONTEXT': 'The occupation may differ from your preferred work setting',
  'R-RELATED': 'Your academic profile may require additional preparation',
}

export function isRecommendationRun(value: unknown): value is RecommendationRun {
  if (!value || typeof value !== 'object') return false
  const record = value as Record<string, unknown>
  if (typeof record.id !== 'string' || !Array.isArray(record.items)) return false
  return record.items.every((item) => {
    if (!item || typeof item !== 'object') return false
    const row = item as Record<string, unknown>
    return (
      typeof row.id === 'string' &&
      typeof row.rank === 'number' &&
      typeof row.title === 'string' &&
      typeof row.onetsoc_code === 'string' &&
      typeof row.explanation === 'string' &&
      typeof row.recommendation_score === 'number' &&
      typeof row.raw_similarity === 'number'
    )
  })
}

export function orderedItems(run: RecommendationRun): RecommendationItem[] {
  return [...run.items].sort((left, right) => {
    if (left.rank !== right.rank) return left.rank - right.rank
    return left.onetsoc_code.localeCompare(right.onetsoc_code)
  })
}

export function blockLabel(block: string): string {
  return BLOCK_LABELS[block] ?? block.replaceAll('_', ' ')
}

export function groupedContributions(features: FeatureContribution[]): Array<{
  block: string
  label: string
  items: FeatureContribution[]
}> {
  const groups: Array<{ block: string; label: string; items: FeatureContribution[] }> = []
  for (const feature of features) {
    const existing = groups.find((group) => group.block === feature.block)
    if (existing) {
      existing.items.push(feature)
    } else {
      groups.push({ block: feature.block, label: blockLabel(feature.block), items: [feature] })
    }
  }
  return groups
}

export function formatSimilarity(value: number): string {
  return value.toFixed(3)
}

export function matchPhrase(rank: number): string {
  return rank === 1 ? 'Closest profile match' : 'Strong profile match'
}

export function flagHeading(flag: RuleFlag): string {
  return FLAG_HEADINGS[flag.rule_code] ?? (flag.action === 'penalise' ? 'This match was adjusted' : 'Something to consider')
}

export function visibleFlags(item: RecommendationItem): RuleFlag[] {
  return [...item.rule_flags, ...item.penalties]
}

export function recommendationLoadError(error: Pick<ApiError, 'status' | 'code' | 'message'>): string {
  if (error.status === 401 || error.code === 'unauthenticated') {
    return 'Your session has expired. Please log in again to view your recommendations.'
  }
  if (error.status === 403 || error.code === 'forbidden') {
    return 'You cannot view another student\'s recommendation run.'
  }
  if (error.status === 404 || error.code === 'invalid_recommendation_run') {
    return 'This recommendation run was not found.'
  }
  if (error.code === 'network_error') {
    return error.message
  }
  return error.message || 'The recommendation could not be loaded.'
}

export function ratingErrorMessage(error: Pick<ApiError, 'status' | 'code' | 'message'>): string {
  if (error.status === 401 || error.code === 'unauthenticated') {
    return 'Your session has expired. Please log in again to send feedback.'
  }
  if (error.status === 403 || error.code === 'forbidden') {
    return 'You cannot rate another student’s recommendation.'
  }
  if (error.status === 422 || error.code === 'validation_error') {
    return 'Choose a relevance rating from 1 to 5.'
  }
  if (error.code === 'network_error') {
    return error.message
  }
  return error.message || 'The rating could not be saved.'
}

export function neighbors(items: RecommendationItem[], itemId: string): {
  current: RecommendationItem | undefined
  previous: RecommendationItem | undefined
  next: RecommendationItem | undefined
} {
  const index = items.findIndex((item) => item.id === itemId)
  return {
    current: index >= 0 ? items[index] : undefined,
    previous: index > 0 ? items[index - 1] : undefined,
    next: index >= 0 && index < items.length - 1 ? items[index + 1] : undefined,
  }
}
