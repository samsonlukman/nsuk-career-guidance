import type { RecommendationItem } from '../../types/recommendations'
import { visibleFlags } from '../../utils/recommendations'
import { ButtonLink } from '../Button'
import { RuleFlagList } from './RuleFlagList'
import { SimilarityScore } from './SimilarityScore'

type RecommendationCardProps = {
  runId: string
  item: RecommendationItem
}

export function RecommendationCard({ runId, item }: RecommendationCardProps) {
  const flags = visibleFlags(item)

  return (
    <article className="recommendation-card">
      <header className="recommendation-card-header">
        <p className="eyebrow">Rank {item.rank}</p>
        <h2>
          <span className="visually-hidden">Rank {item.rank}: </span>
          {item.title}
        </h2>
        <p className="recommendation-soc">O*NET-SOC {item.onetsoc_code}</p>
        {item.job_zone != null ? (
          <p className="recommendation-zone">
            Job Zone {item.job_zone}
            {item.job_zone === 5 ? ' · typically needs extensive preparation' : ''}
          </p>
        ) : null}
      </header>
      <SimilarityScore
        rank={item.rank}
        recommendationScore={item.recommendation_score}
        rawSimilarity={item.raw_similarity}
      />
      <section aria-labelledby={`why-${item.id}`}>
        <h3 id={`why-${item.id}`}>Why this was recommended</h3>
        <p>{item.explanation}</p>
      </section>
      <RuleFlagList flags={flags} />
      <div className="hero-actions">
        <ButtonLink to={`/recommendations/${runId}/items/${item.id}`}>View Career Details</ButtonLink>
      </div>
    </article>
  )
}
