import { useEffect, useState } from 'react'

import { fetchDashboard } from '../api/me'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert } from '../components/Alert'
import { ButtonLink } from '../components/Button'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import type { Dashboard } from '../types/api'
import { hasAssessmentDraft } from '../utils/assessmentAnswers'
import { assessmentStatusLabel, displayName } from '../utils/displayName'
import { formatDateTime } from '../utils/formatDate'

export function DashboardPage() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchDashboard()
      .then((data) => {
        if (!cancelled) setDashboard(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load your dashboard.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return <Spinner label="Loading your dashboard" />
  }

  if (error) {
    return <Alert>{error}</Alert>
  }

  if (!dashboard || !user) {
    return <Alert>Your session could not be loaded.</Alert>
  }

  const completed = dashboard.has_completed_assessment
  const latest = dashboard.latest_assessment
  const latestRun = dashboard.latest_recommendation

  return (
    <article className="dashboard">
      <PageHeader
        title={`Welcome, ${displayName(user)}`}
        description="This page shows your assessment status and recommendation history from the server. Nothing here is invented for display."
      />

      <section className="status-panel" aria-labelledby="assessment-status-heading">
        <h2 id="assessment-status-heading">Assessment status</h2>
        <p className="status-label">{assessmentStatusLabel(completed, latest?.status)}</p>
        {latest ? (
          <dl className="meta-list">
            <div>
              <dt>Last activity</dt>
              <dd>{formatDateTime(latest.completed_at ?? latest.started_at)}</dd>
            </div>
            <div>
              <dt>Questionnaire</dt>
              <dd>{latest.questionnaire_version ?? '—'}</dd>
            </div>
          </dl>
        ) : (
          <EmptyState title="You have not started an assessment">
            <p>
              Complete the career assessment to generate a recommendation run. Until you submit,
              nothing is stored as an assessment on the server.
            </p>
          </EmptyState>
        )}
        <ButtonLink to="/assessment">
          {hasAssessmentDraft(user.id)
            ? 'Continue your career assessment'
            : completed
              ? 'Start a new assessment'
              : 'Start your career assessment'}
        </ButtonLink>
      </section>

      <section aria-labelledby="recommendation-status-heading">
        <h2 id="recommendation-status-heading">Latest recommendation</h2>
        {latestRun ? (
          <>
          <dl className="meta-list">
            <div>
              <dt>Generated</dt>
              <dd>{formatDateTime(latestRun.created_at)}</dd>
            </div>
            <div>
              <dt>Occupations returned</dt>
              <dd>{latestRun.item_count}</dd>
            </div>
            {latestRun.top_occupation_title ? (
              <div>
                <dt>Highest-ranked occupation</dt>
                <dd>
                  {latestRun.top_occupation_title}
                  {latestRun.top_onetsoc_code ? ` (${latestRun.top_onetsoc_code})` : ''}
                </dd>
              </div>
            ) : null}
            <div>
              <dt>Versions</dt>
              <dd>
                {latestRun.questionnaire_version} · {latestRun.feature_version} · {latestRun.config_version}
              </dd>
            </div>
          </dl>
          <ButtonLink to={`/recommendations/${latestRun.run_id}`}>View Recommendations</ButtonLink>
          </>
        ) : (
          <EmptyState title="No recommendation run yet">
            <p>
              Recommendations appear only after a completed assessment is processed by the API.
              Scores will reflect occupational similarity, not predicted career success.
            </p>
          </EmptyState>
        )}
      </section>

      <section aria-labelledby="history-heading">
        <h2 id="history-heading">Previous recommendation history</h2>
        {dashboard.recommendation_history.length === 0 ? (
          <p>There is no stored recommendation history for this account.</p>
        ) : (
          <table className="history-table">
            <caption className="visually-hidden">Stored recommendation runs</caption>
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Items</th>
                <th scope="col">Top occupation</th>
                <th scope="col">Versions</th>
                <th scope="col">Results</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.recommendation_history.map((item) => (
                <tr key={item.run_id}>
                  <td>{formatDateTime(item.created_at)}</td>
                  <td>{item.item_count}</td>
                  <td>{item.top_occupation_title ?? '—'}</td>
                  <td>
                    {item.questionnaire_version} / {item.feature_version}
                  </td>
                  <td>
                    <ButtonLink to={`/recommendations/${item.run_id}`} variant="ghost">
                      View
                    </ButtonLink>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </article>
  )
}
