import { Link, useParams } from 'react-router-dom'

import { Alert } from '../components/Alert'
import { ButtonLink } from '../components/Button'
import { ExperienceEvaluationForm } from '../components/experience/ExperienceEvaluationForm'
import { PageHeader } from '../components/PageHeader'

export function ExperienceEvaluationPage() {
  const { runId } = useParams()

  if (!runId) {
    return (
      <article className="results-page">
        <Alert>These career results were not found.</Alert>
        <ButtonLink to="/dashboard" variant="secondary">
          Back to Dashboard
        </ButtonLink>
      </article>
    )
  }

  return (
    <article className="results-page experience-evaluation-page">
      <PageHeader
        eyebrow="Your feedback"
        title="Evaluate Your Experience"
        description="Please tell us how easy the system was to use, how useful it felt, and whether the recommendations seemed relevant to you. This is not an accuracy test, and it does not change your career recommendations."
      />
      <ExperienceEvaluationForm runId={runId} />
      <div className="hero-actions">
        <ButtonLink to={`/recommendations/${runId}`} variant="secondary">
          Back to recommendations
        </ButtonLink>
        <ButtonLink to="/dashboard" variant="ghost">
          Back to Dashboard
        </ButtonLink>
      </div>
      <p>
        If your session has expired, <Link to="/login">return to log in</Link>.
      </p>
    </article>
  )
}
