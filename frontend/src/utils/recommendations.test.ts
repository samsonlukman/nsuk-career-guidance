import { describe, expect, test } from 'vitest'

import { mockRecommendationRun } from '../test/recommendationFixture'
import {
  blockLabel,
  flagHeading,
  formatSimilarity,
  groupedContributions,
  isRecommendationRun,
  matchPhrase,
  neighbors,
  orderedItems,
  recommendationLoadError,
} from './recommendations'

describe('recommendation helpers', () => {
  test('orders items by persisted rank', () => {
    expect(orderedItems(mockRecommendationRun).map((item) => item.rank)).toEqual([1, 2, 3])
  })

  test('groups contributions with official block labels', () => {
    const top = orderedItems(mockRecommendationRun)[0]
    expect(groupedContributions(top.contributing_features).map((group) => group.label)).toEqual([
      'Specific Interests',
      'Knowledge',
      'Skills',
    ])
    expect(blockLabel('work_styles')).toBe('Work Styles')
  })

  test('formats similarity as a score, not a percentage', () => {
    expect(formatSimilarity(0.83274866)).toBe('0.833')
    expect(matchPhrase(1)).toBe('Closest profile match')
  })

  test('uses constructive flag wording without exposing rule codes in the heading', () => {
    expect(flagHeading({ rule_code: 'R-ZONE-5', action: 'flag', reason: 'Graduate training', penalty: null, element_id: null, domain: null })).toBe(
      'Additional education may be appropriate',
    )
    expect(flagHeading({ rule_code: 'R-CONTEXT', action: 'penalise', reason: 'Public contact', penalty: 0.9, element_id: null, domain: null })).toBe(
      'The occupation may differ from your preferred work setting',
    )
  })

  test('rejects a malformed recommendation payload', () => {
    expect(isRecommendationRun({ id: 'x' })).toBe(false)
    expect(isRecommendationRun(mockRecommendationRun)).toBe(true)
  })

  test('maps load errors for students', () => {
    expect(recommendationLoadError({ status: 403, code: 'forbidden', message: 'Not allowed' })).toMatch(
      /another student/,
    )
    expect(recommendationLoadError({ status: 404, code: 'invalid_recommendation_run', message: 'missing' })).toMatch(
      /not found/,
    )
  })

  test('finds previous and next items from rank order', () => {
    const items = orderedItems(mockRecommendationRun)
    const around = neighbors(items, items[1].id)
    expect(around.previous?.rank).toBe(1)
    expect(around.next?.rank).toBe(3)
  })
})
