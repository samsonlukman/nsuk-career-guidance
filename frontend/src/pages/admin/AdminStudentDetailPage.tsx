import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { fetchAdminStudent } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { ButtonLink } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminStudentDetail } from '../../types/admin'
import { formatDateTime } from '../../utils/formatDate'

export function AdminStudentDetailPage() {
  const { studentId } = useParams()
  const [data, setData] = useState<AdminStudentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!studentId) {
      setError('This student was not found.')
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    fetchAdminStudent(studentId)
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'The student record could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [studentId])

  if (loading) return <Spinner label="Loading student" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>This student was not found.</Alert>

  const name = [data.profile.first_name, data.profile.last_name].filter(Boolean).join(' ') || data.email

  return (
    <article className="admin-page">
      <PageHeader eyebrow="Student record" title={name} description="Stored profile, assessments, and recommendation history. Recommendation results are not edited here." />
      <dl className="meta-list">
        <div>
          <dt>Email</dt>
          <dd>{data.email}</dd>
        </div>
        <div>
          <dt>Matriculation number</dt>
          <dd>{data.profile.matric_number ?? '—'}</dd>
        </div>
        <div>
          <dt>Faculty</dt>
          <dd>{data.profile.faculty ?? '—'}</dd>
        </div>
        <div>
          <dt>Department</dt>
          <dd>{data.profile.department ?? '—'}</dd>
        </div>
        <div>
          <dt>Level</dt>
          <dd>{data.profile.level ?? '—'}</dd>
        </div>
        <div>
          <dt>Account created</dt>
          <dd>{formatDateTime(data.created_at)}</dd>
        </div>
        <div>
          <dt>Last login</dt>
          <dd>{formatDateTime(data.last_login_at)}</dd>
        </div>
      </dl>

      <section aria-labelledby="student-assessments-heading">
        <h2 id="student-assessments-heading">Assessments</h2>
        {data.assessments.length === 0 ? (
          <EmptyState title="No assessments">
            <p>This student has not submitted an assessment.</p>
          </EmptyState>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th scope="col">Status</th>
                <th scope="col">Questionnaire</th>
                <th scope="col">Started</th>
                <th scope="col">Completed</th>
              </tr>
            </thead>
            <tbody>
              {data.assessments.map((item) => (
                <tr key={item.id}>
                  <td>{item.status}</td>
                  <td>{item.questionnaire_version ?? '—'}</td>
                  <td>{formatDateTime(item.started_at)}</td>
                  <td>{formatDateTime(item.completed_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section aria-labelledby="student-runs-heading">
        <h2 id="student-runs-heading">Recommendation history</h2>
        {data.recommendation_history.length === 0 ? (
          <EmptyState title="No recommendation runs">
            <p>Runs appear after a completed assessment is processed by the API.</p>
          </EmptyState>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Top occupation</th>
                <th scope="col">Items</th>
                <th scope="col">Versions</th>
              </tr>
            </thead>
            <tbody>
              {data.recommendation_history.map((item) => (
                <tr key={item.run_id}>
                  <td>{formatDateTime(item.created_at)}</td>
                  <td>
                    <Link to={`/admin/recommendations/${item.run_id}`}>
                      {item.top_occupation_title ?? 'View run'}
                    </Link>
                  </td>
                  <td>{item.item_count}</td>
                  <td>
                    {item.questionnaire_version} · {item.config_version} · {item.onet_release ?? item.feature_version}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      <p>
        <ButtonLink to="/admin/students" variant="secondary">
          Back to students
        </ButtonLink>
      </p>
    </article>
  )
}
