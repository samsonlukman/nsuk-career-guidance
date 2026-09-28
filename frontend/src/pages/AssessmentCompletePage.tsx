import { useLocation } from 'react-router-dom'

import type { AssessmentSubmitConfirmation } from '../types/questionnaire'
import { Alert } from '../components/Alert'
import { ButtonLink } from '../components/Button'
import { PageHeader } from '../components/PageHeader'
import { formatDateTime } from '../utils/formatDate'

function isConfirmation(value: unknown): value is AssessmentSubmitConfirmation {
  if (!value || typeof value !== 'object') return false
  const record = value as Record<string, unknown>
  return typeof record.id === 'string' && typeof record.questionnaire_version === 'string'
}

export function AssessmentCompletePage() {
  const location = useLocation()
  const confirmation = isConfirmation(location.state) ? location.state : null

  return (
    <article className="prose-page">
      <PageHeader
        eyebrow="Assessment submitted"
        title="Your answers were sent to the recommendation service"
        description="The server has stored this assessment and created a recommendation run. Open the results to read the occupations returned by the API."
      />
      {confirmation ? (
        <dl className="meta-list">
          <div>
            <dt>Recommendation run</dt>
            <dd>{confirmation.id}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{formatDateTime(confirmation.created_at)}</dd>
          </div>
          <div>
            <dt>Questionnaire</dt>
            <dd>{confirmation.questionnaire_version}</dd>
          </div>
          <div>
            <dt>Occupations stored for later review</dt>
            <dd>{confirmation.item_count}</dd>
          </div>
        </dl>
      ) : (
        <Alert tone="info">
          If you arrived here without submitting, start from the questionnaire. No placeholder
          occupations are shown.
        </Alert>
      )}
      <p>
        Previous recommendation runs stay in your history. Starting another assessment does not
        delete this one.
      </p>
      <div className="hero-actions">
        {confirmation ? (
          <ButtonLink to={`/recommendations/${confirmation.id}`}>View My Career Recommendations</ButtonLink>
        ) : null}
        <ButtonLink to="/dashboard" variant={confirmation ? 'secondary' : 'primary'}>
          Back to Dashboard
        </ButtonLink>
        <ButtonLink to="/assessment" variant="ghost">
          Start New Assessment
        </ButtonLink>
      </div>
    </article>
  )
}
