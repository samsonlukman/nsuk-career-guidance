import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError } from '../api/client'
import { fetchExperienceEvaluation, fetchRecommendationRun, submitExperienceEvaluation } from '../api/recommendations'
import { Alert } from '../components/Alert'
import { Button, ButtonLink } from '../components/Button'
import { FormField } from '../components/FormField'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import type { ExperienceEvaluationOut } from '../types/recommendations'
import {
  EMPTY_EXPERIENCE_ANSWERS,
  EXPERIENCE_SCALE,
  EXPERIENCE_SCALE_ITEMS,
  experienceEvaluationLoadError,
  experienceEvaluationSubmitError,
  missingExperienceFields,
  type ExperienceEvaluationAnswers,
  type ExperienceScaleField,
} from '../utils/experienceEvaluation'
import { isRecommendationRun } from '../utils/recommendations'

function answersFromSaved(saved: ExperienceEvaluationOut): ExperienceEvaluationAnswers {
  return {
    questions_easy_to_understand: saved.questions_easy_to_understand,
    assessment_easy_to_complete: saved.assessment_easy_to_complete,
    system_easy_to_navigate: saved.system_easy_to_navigate,
    recommendations_easy_to_understand: saved.recommendations_easy_to_understand,
    explanations_helped: saved.explanations_helped,
    reflected_interests: saved.reflected_interests,
    reflected_skills: saved.reflected_skills,
    helped_explore_options: saved.helped_explore_options,
    would_use_again: saved.would_use_again,
    would_discuss_with_counsellor: saved.would_discuss_with_counsellor,
    liked_most_and_improvement: saved.liked_most_and_improvement ?? '',
  }
}

export function ExperienceEvaluationPage() {
  const { runId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [answers, setAnswers] = useState<ExperienceEvaluationAnswers>(EMPTY_EXPERIENCE_ANSWERS)
  const [saved, setSaved] = useState<ExperienceEvaluationOut | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) {
      setError('This recommendation run was not found.')
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchRecommendationRun(runId)
      .then(async (run) => {
        if (cancelled) return
        if (!isRecommendationRun(run)) {
          setError('The recommendation data could not be displayed.')
          return
        }
        try {
          const existing = await fetchExperienceEvaluation(runId)
          if (!cancelled) {
            setSaved(existing)
            setAnswers(answersFromSaved(existing))
          }
        } catch (err) {
          if (cancelled) return
          if (err instanceof ApiError && err.code === 'experience_evaluation_not_found') {
            setSaved(null)
            setAnswers(EMPTY_EXPERIENCE_ANSWERS)
            return
          }
          throw err
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiError = err instanceof ApiError ? err : { message: 'The experience evaluation could not be loaded.' }
        setError(experienceEvaluationLoadError(apiError))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [runId])

  function setScale(field: ExperienceScaleField, value: number) {
    setAnswers((current) => ({ ...current, [field]: value }))
    setSubmitError(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!runId || submitting || saved) return
    const missing = missingExperienceFields(answers)
    if (missing.length > 0) {
      setSubmitError('Please answer every question on the 1 to 5 scale before submitting.')
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    try {
      const result = await submitExperienceEvaluation(runId, {
        questions_easy_to_understand: answers.questions_easy_to_understand as number,
        assessment_easy_to_complete: answers.assessment_easy_to_complete as number,
        system_easy_to_navigate: answers.system_easy_to_navigate as number,
        recommendations_easy_to_understand: answers.recommendations_easy_to_understand as number,
        explanations_helped: answers.explanations_helped as number,
        reflected_interests: answers.reflected_interests as number,
        reflected_skills: answers.reflected_skills as number,
        helped_explore_options: answers.helped_explore_options as number,
        would_use_again: answers.would_use_again as number,
        would_discuss_with_counsellor: answers.would_discuss_with_counsellor as number,
        liked_most_and_improvement: answers.liked_most_and_improvement.trim() || null,
      })
      setSaved(result)
    } catch (err) {
      const apiError = err instanceof ApiError ? err : { message: 'The evaluation could not be saved.' }
      setSubmitError(experienceEvaluationSubmitError(apiError))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <Spinner label="Loading the experience evaluation" />
  }

  if (error) {
    return (
      <article className="results-page">
        <Alert>{error}</Alert>
        {error.includes('session has expired') ? (
          <p>
            <Link to="/login">Return to log in</Link>
          </p>
        ) : null}
        <ButtonLink to="/dashboard" variant="secondary">
          Back to Dashboard
        </ButtonLink>
      </article>
    )
  }

  return (
    <article className="results-page experience-evaluation-page">
      <PageHeader
        eyebrow="Student experience"
        title="Evaluate Your Experience"
        description="Please tell us how easy the system was to use, how useful it felt, and whether the recommendations seemed relevant to you. This is not an accuracy test, and it does not change your career recommendations."
      />
      <p className="scale-key">
        Scale: 1 = Strongly Disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly Agree
      </p>
      {saved ? <Alert tone="info">{saved.note}</Alert> : null}
      {submitError ? <Alert>{submitError}</Alert> : null}
      <form className="form experience-form" onSubmit={(event) => void handleSubmit(event)} noValidate>
        {EXPERIENCE_SCALE_ITEMS.map((item, index) => (
          <fieldset key={item.field} className="question-fieldset experience-question">
            <legend>
              {index + 1}. {item.prompt}
            </legend>
            <div className="likert-options" role="radiogroup" aria-label={item.prompt}>
              {EXPERIENCE_SCALE.map((option) => {
                const id = `${item.field}-${option.value}`
                return (
                  <label key={option.value} className="likert-option" htmlFor={id}>
                    <input
                      id={id}
                      type="radio"
                      name={item.field}
                      value={option.value}
                      checked={answers[item.field] === option.value}
                      disabled={Boolean(saved)}
                      onChange={() => setScale(item.field, option.value)}
                    />
                    <span className="likert-number">{option.value}</span>
                    <span className="likert-label">{option.label}</span>
                  </label>
                )
              })}
            </div>
          </fieldset>
        ))}
        <FormField
          id="liked_most_and_improvement"
          label="11. What did you like most about the system, and what improvement would you suggest?"
          hint="Optional. You may leave this blank."
        >
          <textarea
            id="liked_most_and_improvement"
            name="liked_most_and_improvement"
            rows={4}
            maxLength={2000}
            value={answers.liked_most_and_improvement}
            disabled={Boolean(saved)}
            onChange={(event) =>
              setAnswers((current) => ({ ...current, liked_most_and_improvement: event.target.value }))
            }
          />
        </FormField>
        {!saved ? (
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Saving evaluation…' : 'Submit evaluation'}
          </Button>
        ) : (
          <p className="field-hint">Thank you. Your experience evaluation for this recommendation run has been saved.</p>
        )}
      </form>
      <div className="hero-actions">
        {runId ? (
          <ButtonLink to={`/recommendations/${runId}`} variant="secondary">
            Back to recommendations
          </ButtonLink>
        ) : null}
        <ButtonLink to="/dashboard" variant="ghost">
          Back to Dashboard
        </ButtonLink>
      </div>
    </article>
  )
}
