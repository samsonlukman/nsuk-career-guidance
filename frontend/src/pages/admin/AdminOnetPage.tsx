import { useEffect, useState } from 'react'

import { fetchAdminOnetSnapshot } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminOnetSnapshot } from '../../types/admin'

export function AdminOnetPage() {
  const [data, setData] = useState<AdminOnetSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchAdminOnetSnapshot()
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'The O*NET snapshot could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) return <Spinner label="Loading O*NET snapshot" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>No active O*NET snapshot is available.</Alert>

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Occupational data"
        title="Active O*NET snapshot"
        description="Read-only view of the processed snapshot used by recommendations. Occupational rows cannot be edited here."
      />
      <Alert tone="info">{data.note}</Alert>
      <dl className="meta-list">
        <div>
          <dt>O*NET release</dt>
          <dd>{data.onet_release ?? '—'}</dd>
        </div>
        <div>
          <dt>Release month</dt>
          <dd>{data.onet_release_month ?? '—'}</dd>
        </div>
        <div>
          <dt>Feature version</dt>
          <dd>{data.feature_version ?? '—'}</dd>
        </div>
        <div>
          <dt>Snapshot ID</dt>
          <dd>{data.snapshot_id ?? '—'}</dd>
        </div>
        <div>
          <dt>Occupations</dt>
          <dd>{data.occupation_count}</dd>
        </div>
        <div>
          <dt>Recommendable occupations</dt>
          <dd>{data.recommendable_count}</dd>
        </div>
        <div>
          <dt>KNN feature count</dt>
          <dd>{data.knn_feature_count}</dd>
        </div>
      </dl>
      <section aria-labelledby="job-zone-admin-heading">
        <h2 id="job-zone-admin-heading">Job Zone information</h2>
        <p>Job Zone indicates the level of education, experience, and preparation typically associated with an occupation.</p>
        <table className="history-table">
          <thead>
            <tr>
              <th scope="col">Zone</th>
              <th scope="col">Name</th>
              <th scope="col">Occupations</th>
              <th scope="col">Recommendable</th>
            </tr>
          </thead>
          <tbody>
            {data.job_zones.map((zone) => (
              <tr key={zone.job_zone}>
                <td>{zone.job_zone}</td>
                <td>
                  {zone.name}
                  {zone.education ? <div className="admin-subtle">{zone.education}</div> : null}
                </td>
                <td>{zone.occupation_count}</td>
                <td>{zone.recommendable_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </article>
  )
}
