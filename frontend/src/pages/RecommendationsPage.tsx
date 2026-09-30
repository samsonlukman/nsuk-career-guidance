import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError } from '../api/client'
import { fetchExperienceEvaluation, fetchRecommendationRun } from '../api/recommendations'
import { Alert } from '../components/Alert'
import { Button, ButtonLink } from '../components/Button'
import { ExperienceEvaluationModal } from '../components/experience/ExperienceEvaluationModal'
import { RecommendationCard } from '../components/recommendations/RecommendationCard'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import type { RecommendationRun } from '../types/recommendations'
import { hasSeenExperienceEvaluation, markExperienceEvaluationSeen } from '../utils/experienceEvaluationPrompt'
import { formatDateTime } from '../utils/formatDate'
import { isRecommendationRun, orderedItems, recommendationLoadError } from '../utils/recommendations'
import { studentFacingNotes } from '../utils/studentFacingText'

export function RecommendationsPage() {
  const { runId } = useParams()
  const [run, setRun] = useState<RecommendationRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [evaluateOpen, setEvaluateOpen] = useState(false)

  const openEvaluation = useCallback(() => {
    if (!runId) return
    markExperienceEvaluationSeen(runId)
    setEvaluateOpen(true)
  }, [runId])

  const closeEvaluation = useCallback(() => {
    if (runId) markExperienceEvaluationSeen(runId)
    setEvaluateOpen(false)
  }, [runId])

  useEffect(() => {
    if (!runId) {
      setError('These career results were not found.')
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
          setError('Your career results could not be displayed.')
          setRun(null)
          return
        }
        setRun(data)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiError = err instanceof ApiError ? err : { message: 'Your career results could not be loaded.' }
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
    if (!runId || !run) return
    let cancelled = false
    fetchExperienceEvaluation(runId)
      .then(() => {
        if (!cancelled) markExperienceEvaluationSeen(runId)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.code === 'experience_evaluation_not_found') {
          if (!hasSeenExperienceEvaluation(runId)) {
            markExperienceEvaluationSeen(runId)
            setEvaluateOpen(true)
          }
        }
      })
    return () => {
      cancelled = true
    }
  }, [run, runId])

  const items = useMemo(() => (run ? orderedItems(run) : []), [run])
  const notes = useMemo(() => (run ? studentFacingNotes(run.notes) : []), [run])

  if (loading) {
    return <Spinner label="Loading your recommendations" />
  }

  if (error || !run) {
    return (
      <article className="results-page">
        <Alert>{error ?? 'Your career results could not be loaded.'}</Alert>
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
        eyebrow="Your results"
        title="Your Career Recommendations"
        description="These careers were selected by comparing your assessment answers with occupational information. They are meant to support career exploration and decision-making. They do not guarantee success, predict employment, or determine your career."
      />
      <dl className="meta-list">
        <div>
          <dt>Prepared</dt>
          <dd>{formatDateTime(run.created_at)}</dd>
        </div>
        <div>
          <dt>Recommendations shown</dt>
          <dd>{items.length}</dd>
        </div>
      </dl>
      {notes.map((note) => (
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
        <Button onClick={openEvaluation}>Evaluate Your Experience</Button>
        <ButtonLink to="/dashboard" variant="secondary">
          Back to Dashboard
        </ButtonLink>
        <ButtonLink to="/assessment" variant="ghost">
          Start New Assessment
        </ButtonLink>
      </div>
      <ExperienceEvaluationModal runId={run.id} open={evaluateOpen} onClose={closeEvaluation} />
    </article>
  )
}
