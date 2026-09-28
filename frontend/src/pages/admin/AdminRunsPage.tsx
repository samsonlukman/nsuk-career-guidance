import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { fetchAdminRuns } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { Pagination } from '../../components/admin/Pagination'
import { EmptyState } from '../../components/EmptyState'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminRunList } from '../../types/admin'
import { formatDateTime } from '../../utils/formatDate'

export function AdminRunsPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page') || '1')
  const [data, setData] = useState<AdminRunList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchAdminRuns({ page, page_size: 20 })
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Recommendation activity could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page])

  if (loading) return <Spinner label="Loading recommendation activity" />
  if (error) return <Alert>{error}</Alert>
  if (!data || data.items.length === 0) {
    return (
      <article className="admin-page">
        <PageHeader
          title="Recommendation activity"
          description="Persisted recommendation runs from completed assessments. This view does not recompute matches."
        />
        <EmptyState title="No recommendation runs">
          <p>Runs appear after students complete an assessment.</p>
        </EmptyState>
      </article>
    )
  }

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Inspection"
        title="Recommendation activity"
        description="Persisted recommendation runs from completed assessments. This view does not recompute matches."
      />
      <table className="history-table">
        <caption className="visually-hidden">Stored recommendation runs</caption>
        <thead>
          <tr>
            <th scope="col">Student</th>
            <th scope="col">Assessment date</th>
            <th scope="col">Top occupation</th>
            <th scope="col">Items</th>
            <th scope="col">Versions</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((item) => (
            <tr key={item.run_id}>
              <td>
                <Link to={`/admin/students/${item.student_id}`}>{item.student_name || item.student_email}</Link>
                <div className="admin-subtle">{item.student_email}</div>
              </td>
              <td>{formatDateTime(item.assessment_completed_at ?? item.created_at)}</td>
              <td>
                <Link to={`/admin/recommendations/${item.run_id}`}>
                  {item.top_occupation_title ?? 'View stored run'}
                </Link>
                {item.top_onetsoc_code ? <div className="admin-subtle">{item.top_onetsoc_code}</div> : null}
              </td>
              <td>{item.item_count}</td>
              <td>
                {item.questionnaire_version} · {item.config_version} · {item.onet_release ?? item.feature_version}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination
        page={data.page}
        totalPages={data.total_pages}
        onPageChange={(nextPage) => {
          const next = new URLSearchParams(params)
          next.set('page', String(nextPage))
          setParams(next)
        }}
      />
    </article>
  )
}
