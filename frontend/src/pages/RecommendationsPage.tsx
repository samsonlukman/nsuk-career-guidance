import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError } from '../api/client'
import { fetchRecommendationRun } from '../api/recommendations'
import { Alert } from '../components/Alert'
import { ButtonLink } from '../components/Button'
import { RecommendationCard } from '../components/recommendations/RecommendationCard'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import type { RecommendationRun } from '../types/recommendations'
import { formatDateTime } from '../utils/formatDate'
import { isRecommendationRun, orderedItems, recommendationLoadError } from '../utils/recommendations'

export function RecommendationsPage() {
  const { runId } = useParams()
  const [run, setRun] = useState<RecommendationRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) {
      setError('This recommendation run was not found.')
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchRecommendationRun(runId)
      .then((data) => {
        if (cancelled) return
        if (!isRecommendationRun(data)) {
          setError('The recommendation data could not be displayed.')
          setRun(null)
          return
        }
        setRun(data)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiError = err instanceof ApiError ? err : { message: 'The recommendation could not be loaded.' }
        setError(recommendationLoadError(apiError))
        setRun(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [runId])

  const items = useMemo(() => (run ? orderedItems(run) : []), [run])

  if (loading) {
    return <Spinner label="Loading your recommendations" />
  }

  if (error || !run) {
    return (
      <article className="results-page">
        <Alert>{error ?? 'The recommendation could not be loaded.'}</Alert>
        {error?.includes('session has expired') ? (
          <p>
            <Link to="/login">Return to log in</Link>
          </p>
        ) : null}
        <ButtonLink to="/dashboard" variant="secondary">
          Back to Dashboard
        </ButtonLink>
      </article>
    )
  }

  return (
    <article className="results-page">
      <PageHeader
        eyebrow="Recommendation results"
        title="Your Career Recommendations"
        description="These careers were selected by comparing your assessment profile with occupational characteristics in the O*NET database. They are meant to support career exploration and decision-making. They do not guarantee success, predict employment, or determine your career."
      />
      <dl className="meta-list">
        <div>
          <dt>Generated</dt>
          <dd>{formatDateTime(run.created_at)}</dd>
        </div>
        <div>
          <dt>Recommendations shown</dt>
          <dd>{items.length}</dd>
        </div>
        <div>
          <dt>Questionnaire</dt>
          <dd>{run.questionnaire_version}</dd>
        </div>
      </dl>
      {run.notes.map((note) => (
        <Alert key={note} tone="info">
          {note}
        </Alert>
      ))}
      <ol className="recommendation-list">
        {items.map((item) => (
          <li key={item.id}>
            <RecommendationCard runId={run.id} item={item} />
          </li>
        ))}
      </ol>
      <div className="hero-actions">
        <ButtonLink to="/dashboard" variant="secondary">
          Back to Dashboard
        </ButtonLink>
        <ButtonLink to="/assessment" variant="ghost">
          Start New Assessment
        </ButtonLink>
      </div>
    </article>
  )
}
