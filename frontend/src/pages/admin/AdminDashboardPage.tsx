import { useEffect, useState } from 'react'

import { fetchAdminDashboard } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminDashboard } from '../../types/admin'

export function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchAdminDashboard()
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'The admin dashboard could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) return <Spinner label="Loading administration overview" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>No administration data is available.</Alert>

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Administration"
        title="Admin dashboard"
        description="System counts and active versions come from the FastAPI database. Nothing here is estimated or invented."
      />
      {data.notes.map((note) => (
        <Alert key={note} tone="info">
          {note}
        </Alert>
      ))}
      <section aria-labelledby="admin-counts-heading">
        <h2 id="admin-counts-heading">Stored activity</h2>
        <ul className="admin-stat-grid">
          <li>
            <p className="admin-stat-label">Registered students</p>
            <p className="admin-stat-value">{data.students_total}</p>
          </li>
          <li>
            <p className="admin-stat-label">Completed assessments</p>
            <p className="admin-stat-value">{data.assessments_completed}</p>
          </li>
          <li>
            <p className="admin-stat-label">Recommendation runs</p>
            <p className="admin-stat-value">{data.recommendation_runs}</p>
          </li>
          <li>
            <p className="admin-stat-label">Relevance ratings</p>
            <p className="admin-stat-value">{data.ratings_total}</p>
            <p className="admin-stat-note">
              {data.ratings_average == null
                ? 'No ratings stored yet'
                : `Average relevance ${data.ratings_average} (not accuracy)`}
            </p>
          </li>
        </ul>
      </section>
      <section aria-labelledby="admin-versions-heading">
        <h2 id="admin-versions-heading">Active versions</h2>
        <dl className="meta-list">
          <div>
            <dt>O*NET snapshot</dt>
            <dd>
              {data.active_onet.onet_release ?? 'None'} · {data.active_onet.feature_version ?? '—'} ·{' '}
              {data.active_onet.occupation_count} occupations ({data.active_onet.recommendable_count} recommendable)
            </dd>
          </div>
          <div>
            <dt>Questionnaire</dt>
            <dd>
              {data.active_questionnaire.version ?? 'None'} · {data.active_questionnaire.status ?? '—'} ·{' '}
              {data.active_questionnaire.question_count} questions
            </dd>
          </div>
          <div>
            <dt>Recommendation configuration</dt>
            <dd>
              {data.active_config.version ?? 'None'} · k={data.active_config.k ?? '—'} · {data.active_config.metric ?? '—'}
            </dd>
          </div>
        </dl>
      </section>
      <section aria-labelledby="admin-health-heading">
        <h2 id="admin-health-heading">System status</h2>
        <dl className="meta-list">
          <div>
            <dt>API</dt>
            <dd>{data.system.api}</dd>
          </div>
          <div>
            <dt>Database</dt>
            <dd>{data.system.database}</dd>
          </div>
          <div>
            <dt>Active O*NET snapshot</dt>
            <dd>{data.system.active_onet_snapshot ? 'Available' : 'Missing'}</dd>
          </div>
          <div>
            <dt>Active questionnaire</dt>
            <dd>{data.system.active_questionnaire ? 'Available' : 'Missing'}</dd>
          </div>
          <div>
            <dt>Active recommendation configuration</dt>
            <dd>{data.system.active_recommendation_config ? 'Available' : 'Missing'}</dd>
          </div>
        </dl>
      </section>
    </article>
  )
}
