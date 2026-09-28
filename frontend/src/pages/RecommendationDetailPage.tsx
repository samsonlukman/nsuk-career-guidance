import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError } from '../api/client'
import { fetchOccupation } from '../api/occupations'
import { fetchRecommendationRun } from '../api/recommendations'
import { Alert } from '../components/Alert'
import { ButtonLink } from '../components/Button'
import { ContributionGroups } from '../components/recommendations/ContributionGroups'
import { JobZoneNote } from '../components/recommendations/JobZoneNote'
import { RatingForm } from '../components/recommendations/RatingForm'
import { RuleFlagList } from '../components/recommendations/RuleFlagList'
import { SimilarityScore } from '../components/recommendations/SimilarityScore'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import type { OccupationDetail, RecommendationRun } from '../types/recommendations'
import { isRecommendationRun, neighbors, orderedItems, recommendationLoadError, visibleFlags } from '../utils/recommendations'

export function RecommendationDetailPage() {
  const { runId, itemId } = useParams()
  const [run, setRun] = useState<RecommendationRun | null>(null)
  const [occupation, setOccupation] = useState<OccupationDetail | null>(null)
  const [occupationError, setOccupationError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const items = useMemo(() => (run ? orderedItems(run) : []), [run])
  const { current, previous, next } = useMemo(
    () => neighbors(items, itemId ?? ''),
    [items, itemId],
  )

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

  useEffect(() => {
    if (!current) {
      setOccupation(null)
      setOccupationError(null)
      return
    }
    let cancelled = false
    setOccupation(null)
    setOccupationError(null)
    fetchOccupation(current.onetsoc_code)
      .then((data) => {
        if (!cancelled) setOccupation(data)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setOccupationError(err instanceof ApiError ? err.message : 'Occupation details could not be loaded.')
      })
    return () => {
      cancelled = true
    }
  }, [current])

  if (loading) {
    return <Spinner label="Loading career details" />
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

  if (!current) {
    return (
      <article className="results-page">
        <Alert>This recommendation item was not found in the stored run.</Alert>
        <ButtonLink to={`/recommendations/${run.id}`} variant="secondary">
          Back to recommendations
        </ButtonLink>
      </article>
    )
  }

  const flags = visibleFlags(current)

  return (
    <article className="results-page">
      <PageHeader
        eyebrow={`Rank ${current.rank} of ${items.length}`}
        title={occupation?.title ?? current.title}
        description="Details below come from the stored recommendation run and the O*NET occupation record. Nothing here is invented for display."
      />
      <p className="recommendation-soc">O*NET-SOC {current.onetsoc_code}</p>
      <SimilarityScore
        rank={current.rank}
        recommendationScore={current.recommendation_score}
        rawSimilarity={current.raw_similarity}
      />

      <section aria-labelledby="why-heading">
        <h2 id="why-heading">Why this was recommended</h2>
        <p>{current.explanation}</p>
      </section>

      <section aria-labelledby="factors-heading">
        <h2 id="factors-heading">Contributing factors</h2>
        <p>These are the factors the recommendation record listed as important for this match. They are not equally weighted.</p>
        <ContributionGroups features={current.contributing_features} />
      </section>

      {current.work_activities.length > 0 ? (
        <section aria-labelledby="activities-heading">
          <h2 id="activities-heading">Relevant work activities</h2>
          <ul>
            {current.work_activities.map((activity) => (
              <li key={activity}>{activity}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <JobZoneNote
        jobZone={occupation?.job_zone ?? current.job_zone}
        jobZoneName={occupation?.job_zone_name}
        jobZoneNote={current.job_zone_note}
        jobZoneEducation={occupation?.job_zone_education}
        jobZoneExperience={occupation?.job_zone_experience}
      />

      <RuleFlagList flags={flags} />

      <section aria-labelledby="occupation-heading">
        <h2 id="occupation-heading">Occupation details</h2>
        {occupationError ? <Alert>{occupationError}</Alert> : null}
        {occupation ? (
          <>
            <p>{occupation.description}</p>
            {occupation.education.filter((row) => row.percent > 0).length > 0 ? (
              <>
                <h3>Education reported by incumbents</h3>
                <ul>
                  {occupation.education
                    .filter((row) => row.percent > 0)
                    .map((row) => (
                      <li key={row.category}>
                        {row.description}: {row.percent}% of incumbents
                      </li>
                    ))}
                </ul>
              </>
            ) : null}
            {occupation.work_activities.length > 0 ? (
              <>
                <h3>O*NET work activities</h3>
                <ul>
                  {occupation.work_activities.map((row) => (
                    <li key={row.element_id}>{row.name}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </>
        ) : occupationError ? null : (
          <Spinner label="Loading occupation details" />
        )}
      </section>

      <RatingForm itemId={current.id} />

      <nav className="recommendation-pager" aria-label="Recommendation navigation">
        {previous ? (
          <ButtonLink to={`/recommendations/${run.id}/items/${previous.id}`} variant="secondary">
            Previous: {previous.title}
          </ButtonLink>
        ) : (
          <span />
        )}
        {next ? (
          <ButtonLink to={`/recommendations/${run.id}/items/${next.id}`} variant="secondary">
            Next: {next.title}
          </ButtonLink>
        ) : null}
      </nav>
      <div className="hero-actions">
        <ButtonLink to={`/recommendations/${run.id}`} variant="secondary">
          Back to recommendations
        </ButtonLink>
        <ButtonLink to="/dashboard" variant="ghost">
          Back to Dashboard
        </ButtonLink>
        <ButtonLink to="/assessment" variant="ghost">
          Start New Assessment
        </ButtonLink>
      </div>
    </article>
  )
}
