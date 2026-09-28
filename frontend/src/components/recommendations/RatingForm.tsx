import { useState, type FormEvent } from 'react'

import { ApiError } from '../../api/client'
import { submitRecommendationRating } from '../../api/recommendations'
import type { RatingOut } from '../../types/recommendations'
import { ratingErrorMessage } from '../../utils/recommendations'
import { Alert } from '../Alert'
import { Button } from '../Button'
import { FormField } from '../FormField'

type RatingFormProps = {
  itemId: string
}

const SCALE = [1, 2, 3, 4, 5] as const

export function RatingForm({ itemId }: RatingFormProps) {
  const [value, setValue] = useState<number | null>(null)
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<RatingOut | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    if (value == null) {
      setError('Choose a relevance rating from 1 to 5.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const saved = await submitRecommendationRating(itemId, {
        relevance_1_to_5: value,
        comment: comment.trim() || null,
      })
      setResult(saved)
    } catch (err) {
      const apiError = err instanceof ApiError ? err : { message: 'The rating could not be saved.' }
      setError(ratingErrorMessage(apiError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="rating-form" aria-labelledby="rating-heading">
      <h3 id="rating-heading">Your feedback</h3>
      <p>How relevant is this recommendation to you? Feedback helps evaluate the system later.</p>
      {result ? <Alert tone="info">{result.note}</Alert> : null}
      {error ? <Alert>{error}</Alert> : null}
      <form className="form" onSubmit={(event) => void handleSubmit(event)} noValidate>
        <fieldset className="question-fieldset">
          <legend>Relevance</legend>
          <div className="likert-options" role="radiogroup" aria-label="Relevance from 1 to 5">
            {SCALE.map((score) => {
              const id = `${itemId}-rating-${score}`
              return (
                <label key={score} className="likert-option" htmlFor={id}>
                  <input
                    id={id}
                    type="radio"
                    name={`${itemId}-rating`}
                    value={score}
                    checked={value === score}
                    onChange={() => {
                      setValue(score)
                      setError(null)
                    }}
                  />
                  <span className="likert-number">{score}</span>
                </label>
              )
            })}
          </div>
          <div className="likert-ends">
            <span>Not relevant</span>
            <span>Highly relevant</span>
          </div>
        </fieldset>
        <FormField id={`${itemId}-comment`} label="Optional comment">
          <textarea
            id={`${itemId}-comment`}
            name="comment"
            rows={3}
            maxLength={2000}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
          />
        </FormField>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Saving feedback…' : result ? 'Update feedback' : 'Save feedback'}
        </Button>
      </form>
    </section>
  )
}
