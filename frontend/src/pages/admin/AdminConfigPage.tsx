import { useEffect, useState } from 'react'

import { fetchAdminRecommendationConfig } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminRecommendationConfig } from '../../types/admin'

export function AdminConfigPage() {
  const [data, setData] = useState<AdminRecommendationConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchAdminRecommendationConfig()
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'The recommendation configuration could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) return <Spinner label="Loading recommendation configuration" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>No recommendation configuration is available.</Alert>

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Recommendation engine"
        title="Active configuration"
        description="Read-only display of the stored recommendation configuration. This page cannot change KNN behaviour."
      />
      <Alert tone="info">{data.note}</Alert>
      <dl className="meta-list">
        <div>
          <dt>Configuration version</dt>
          <dd>{data.version ?? '—'}</dd>
        </div>
        <div>
          <dt>k</dt>
          <dd>{data.k ?? '—'}</dd>
        </div>
        <div>
          <dt>Metric</dt>
          <dd>{data.metric ?? '—'}</dd>
        </div>
        <div>
          <dt>Feature version</dt>
          <dd>{data.feature_version ?? '—'}</dd>
        </div>
      </dl>
      <section aria-labelledby="block-weights-heading">
        <h2 id="block-weights-heading">Block weights</h2>
        <table className="history-table">
          <thead>
            <tr>
              <th scope="col">Block</th>
              <th scope="col">Weight</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.block_weights).map(([block, weight]) => (
              <tr key={block}>
                <td>{block}</td>
                <td>{weight}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </article>
  )
}
