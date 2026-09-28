import { useEffect, useState } from 'react'

import { fetchAdminQuestionnaire } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminQuestionnaire } from '../../types/admin'

export function AdminQuestionnairePage() {
  const [data, setData] = useState<AdminQuestionnaire | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchAdminQuestionnaire()
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'The questionnaire could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) return <Spinner label="Loading questionnaire" />
  if (error) return <Alert>{error}</Alert>
  if (!data) return <Alert>No active questionnaire is available.</Alert>

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Questionnaire"
        title="Active questionnaire"
        description="Inspection only. Questions are not edited from this view."
      />
      <Alert tone="info">{data.note}</Alert>
      <dl className="meta-list">
        <div>
          <dt>Version</dt>
          <dd>{data.version ?? '—'}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{data.status ?? '—'}</dd>
        </div>
        <div>
          <dt>Feature version</dt>
          <dd>{data.feature_version ?? '—'}</dd>
        </div>
        <div>
          <dt>Questions</dt>
          <dd>{data.question_count}</dd>
        </div>
        <div>
          <dt>Options</dt>
          <dd>{data.option_count}</dd>
        </div>
      </dl>
      <ol className="admin-question-list">
        {data.questions.map((question) => (
          <li key={question.code}>
            <h2>
              {question.sort_order}. {question.code}
            </h2>
            <p>{question.prompt}</p>
            <p className="admin-subtle">
              {question.section} · {question.response_type}
              {question.block ? ` · ${question.block}` : ''}
              {question.onet_element_id ? ` · ${question.onet_element_id}` : ''}
              {question.is_required ? ' · required' : ''}
              {question.option_count ? ` · ${question.option_count} options` : ''}
            </p>
          </li>
        ))}
      </ol>
    </article>
  )
}
