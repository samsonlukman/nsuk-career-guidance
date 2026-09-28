import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { fetchAdminRun } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { ButtonLink } from '../../components/Button'
import { ContributionGroups } from '../../components/recommendations/ContributionGroups'
import { JobZoneNote } from '../../components/recommendations/JobZoneNote'
import { RuleFlagList } from '../../components/recommendations/RuleFlagList'
import { SimilarityScore } from '../../components/recommendations/SimilarityScore'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminRunDetail } from '../../types/admin'
import { formatDateTime } from '../../utils/formatDate'
import { isRecommendationRun, orderedItems, visibleFlags } from '../../utils/recommendations'

export function AdminRunDetailPage() {
  const { runId } = useParams()
  const [data, setData] = useState<AdminRunDetail | null>(null)
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
    fetchAdminRun(runId)
      .then((payload) => {
        if (cancelled) return
        if (!payload.run || !isRecommendationRun(payload.run)) {
          setError('The recommendation data could not be displayed.')
          return
        }
        setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'The recommendation run could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [runId])

  if (loading) return <Spinner label="Loading stored recommendation run" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>This recommendation run was not found.</Alert>

  const studentName = [data.student.first_name, data.student.last_name].filter(Boolean).join(' ') || data.student.email
  const items = orderedItems(data.run)

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Persisted recommendation run"
        title="Inspect recommendation run"
        description="This is the stored result. The recommendation is not recalculated when this page opens."
      />
      <dl className="meta-list">
        <div>
          <dt>Student</dt>
          <dd>
            {studentName} · {data.student.email}
          </dd>
        </div>
        <div>
          <dt>Stored at</dt>
          <dd>{formatDateTime(data.run.created_at)}</dd>
        </div>
        <div>
          <dt>Questionnaire</dt>
          <dd>{data.run.questionnaire_version}</dd>
        </div>
        <div>
          <dt>Configuration</dt>
          <dd>
            {data.run.config_version} · k={data.run.k} · {data.run.metric}
          </dd>
        </div>
        <div>
          <dt>O*NET</dt>
          <dd>
            {data.run.onet_release ?? '—'} · {data.run.feature_version}
          </dd>
        </div>
      </dl>
      <ol className="recommendation-list">
        {items.map((item) => (
          <li key={item.id}>
            <article className="recommendation-card">
              <header>
                <p className="eyebrow">Rank {item.rank}</p>
                <h2>
                  {item.title} <span className="admin-subtle">({item.onetsoc_code})</span>
                </h2>
              </header>
              <SimilarityScore
                rank={item.rank}
                recommendationScore={item.recommendation_score}
                rawSimilarity={item.raw_similarity}
              />
              <section>
                <h3>Why this was recommended</h3>
                <p>{item.explanation}</p>
              </section>
              <JobZoneNote
                headingId={`job-zone-${item.id}`}
                jobZone={item.job_zone}
                jobZoneNote={item.job_zone_note}
              />
              <RuleFlagList flags={visibleFlags(item)} />
              {item.rule_flags.length + item.penalties.length > 0 ? (
                <p className="admin-subtle">
                  Internal codes:{' '}
                  {[...item.rule_flags, ...item.penalties].map((flag) => flag.rule_code).join(', ')}
                </p>
              ) : null}
              <ContributionGroups features={item.contributing_features} />
            </article>
          </li>
        ))}
      </ol>
      <p>
        <ButtonLink to="/admin/recommendations" variant="secondary">
          Back to recommendation activity
        </ButtonLink>
      </p>
    </article>
  )
}
