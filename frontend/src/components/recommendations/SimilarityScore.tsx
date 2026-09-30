import { formatSimilarity, matchPhrase } from '../../utils/recommendations'

type SimilarityScoreProps = {
  rank: number
  recommendationScore: number
  rawSimilarity: number
}

export function SimilarityScore({ rank, recommendationScore }: SimilarityScoreProps) {
  const bounded = recommendationScore >= 0 && recommendationScore <= 1
  const label = `${matchPhrase(rank)}. Match score ${formatSimilarity(recommendationScore)}.`

  return (
    <div className="similarity-score">
      <p className="similarity-phrase">{matchPhrase(rank)}</p>
      <p className="similarity-label">
        Match score <span className="similarity-value">{formatSimilarity(recommendationScore)}</span>
      </p>
      {bounded ? (
        <div
          className="similarity-track"
          role="meter"
          aria-label="Match score"
          aria-valuemin={0}
          aria-valuemax={1}
          aria-valuenow={Number(recommendationScore.toFixed(3))}
          aria-valuetext={label}
        >
          <div className="similarity-fill" style={{ width: `${recommendationScore * 100}%` }} />
        </div>
      ) : null}
      <p className="field-hint">This score shows how closely the career matches your answers. It is not a prediction of success or employment.</p>
    </div>
  )
}
