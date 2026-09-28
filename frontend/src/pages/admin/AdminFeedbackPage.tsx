import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { fetchAdminRatings } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { Pagination } from '../../components/admin/Pagination'
import { EmptyState } from '../../components/EmptyState'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminRatingList } from '../../types/admin'
import { formatDateTime } from '../../utils/formatDate'

export function AdminFeedbackPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page') || '1')
  const [data, setData] = useState<AdminRatingList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchAdminRatings({ page, page_size: 20 })
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Feedback could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page])

  if (loading) return <Spinner label="Loading recommendation feedback" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>No feedback is available.</Alert>

  const distribution = [1, 2, 3, 4, 5].map((value) => ({
    value,
    count: data.summary.distribution[String(value)] ?? data.summary.distribution[value] ?? 0,
  }))

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Evaluation feedback"
        title="Recommendation feedback"
        description="Students rated how relevant a stored recommendation felt. These values are not a measure of recommendation accuracy."
      />
      <Alert tone="info">{data.summary.note}</Alert>
      <ul className="admin-stat-grid">
        <li>
          <p className="admin-stat-label">Ratings stored</p>
          <p className="admin-stat-value">{data.summary.ratings_total}</p>
        </li>
        <li>
          <p className="admin-stat-label">Average relevance</p>
          <p className="admin-stat-value">
            {data.summary.average_relevance == null ? '—' : data.summary.average_relevance}
          </p>
          <p className="admin-stat-note">1–5 relevance scale, not accuracy</p>
        </li>
      </ul>
      <section aria-labelledby="rating-distribution-heading">
        <h2 id="rating-distribution-heading">Rating distribution</h2>
        <ul className="admin-distribution">
          {distribution.map((item) => (
            <li key={item.value}>
              <span>{item.value} of 5</span>
              <span>{item.count}</span>
            </li>
          ))}
        </ul>
      </section>
      {data.items.length === 0 ? (
        <EmptyState title="No ratings yet">
          <p>Ratings appear after a student submits feedback on a recommendation.</p>
        </EmptyState>
      ) : (
        <table className="history-table">
          <caption className="visually-hidden">Stored relevance ratings</caption>
          <thead>
            <tr>
              <th scope="col">Rating</th>
              <th scope="col">Occupation</th>
              <th scope="col">Student</th>
              <th scope="col">Comment</th>
              <th scope="col">Date</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.id}>
                <td>{item.relevance_1_to_5} of 5</td>
                <td>
                  <Link to={`/admin/recommendations/${item.run_id}`}>
                    {item.occupation_title ?? item.onetsoc_code}
                  </Link>
                </td>
                <td>
                  <Link to={`/admin/students/${item.student_id}`}>{item.student_email}</Link>
                </td>
                <td>{item.comment || '—'}</td>
                <td>{formatDateTime(item.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
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
