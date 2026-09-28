import { formatSimilarity, matchPhrase } from '../../utils/recommendations'

type SimilarityScoreProps = {
  rank: number
  recommendationScore: number
  rawSimilarity: number
}

export function SimilarityScore({ rank, recommendationScore, rawSimilarity }: SimilarityScoreProps) {
  const bounded = recommendationScore >= 0 && recommendationScore <= 1
  const label = `${matchPhrase(rank)}. Profile similarity ${formatSimilarity(recommendationScore)}.`

  return (
    <div className="similarity-score">
      <p className="similarity-phrase">{matchPhrase(rank)}</p>
      <p className="similarity-label">
        Profile similarity <span className="similarity-value">{formatSimilarity(recommendationScore)}</span>
      </p>
      {rawSimilarity !== recommendationScore ? (
        <p className="similarity-raw">Raw similarity {formatSimilarity(rawSimilarity)}</p>
      ) : null}
      {bounded ? (
        <div
          className="similarity-track"
          role="meter"
          aria-label="Profile similarity"
          aria-valuemin={0}
          aria-valuemax={1}
          aria-valuenow={Number(recommendationScore.toFixed(3))}
          aria-valuetext={label}
        >
          <div className="similarity-fill" style={{ width: `${recommendationScore * 100}%` }} />
        </div>
      ) : null}
      <p className="field-hint">This is a profile similarity score, not a prediction of success or employment.</p>
    </div>
  )
}
