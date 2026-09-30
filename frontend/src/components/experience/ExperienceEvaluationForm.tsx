import { useEffect, useState, type FormEvent } from 'react'

import { ApiError } from '../../api/client'
import { fetchExperienceEvaluation, submitExperienceEvaluation } from '../../api/recommendations'
import type { ExperienceEvaluationOut } from '../../types/recommendations'
import {
  EMPTY_EXPERIENCE_ANSWERS,
  EXPERIENCE_SCALE,
  EXPERIENCE_SCALE_ITEMS,
  experienceEvaluationLoadError,
  experienceEvaluationSubmitError,
  missingExperienceFields,
  type ExperienceEvaluationAnswers,
  type ExperienceScaleField,
} from '../../utils/experienceEvaluation'
import { Alert } from '../Alert'
import { Button } from '../Button'
import { FormField } from '../FormField'
import { Spinner } from '../Spinner'

export function answersFromSaved(saved: ExperienceEvaluationOut): ExperienceEvaluationAnswers {
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

type ExperienceEvaluationFormProps = {
  runId: string
  onSaved?: (saved: ExperienceEvaluationOut) => void
}

export function ExperienceEvaluationForm({ runId, onSaved }: ExperienceEvaluationFormProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [answers, setAnswers] = useState<ExperienceEvaluationAnswers>(EMPTY_EXPERIENCE_ANSWERS)
  const [saved, setSaved] = useState<ExperienceEvaluationOut | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchExperienceEvaluation(runId)
      .then((existing) => {
        if (cancelled) return
        setSaved(existing)
        setAnswers(answersFromSaved(existing))
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.code === 'experience_evaluation_not_found') {
          setSaved(null)
          setAnswers(EMPTY_EXPERIENCE_ANSWERS)
          return
        }
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
    if (submitting || saved) return
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
      onSaved?.(result)
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
    return <Alert>{error}</Alert>
  }

  return (
    <>
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
          <p className="field-hint">Thank you. Your experience evaluation has been saved.</p>
        )}
      </form>
    </>
  )
}
