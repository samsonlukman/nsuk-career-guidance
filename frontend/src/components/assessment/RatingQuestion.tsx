import type { Question } from '../../types/questionnaire'
import { ratingScaleOptions } from '../../utils/questionnaire'

type RatingQuestionProps = {
  question: Question
  value: string
  error?: string
  onChange: (value: string) => void
  legend?: string
  name?: string
}

export function RatingQuestion({ question, value, error, onChange, legend, name }: RatingQuestionProps) {
  const options = ratingScaleOptions(question)
  const fieldName = name ?? question.code
  const errorId = `${fieldName}-error`
  const first = options[0]
  const last = options[options.length - 1]
  const minimum = question.min_value
  const maximum = question.max_value

  return (
    <fieldset className="question-fieldset" aria-describedby={error ? errorId : undefined}>
      <legend>{legend ?? question.prompt}</legend>
      {minimum != null && maximum != null ? (
        <p className="field-hint">
          Rate from {minimum} to {maximum}.
        </p>
      ) : null}
      <div className="likert-options" role="radiogroup" aria-label={legend ?? question.prompt}>
        {options.map((option) => {
          const id = `${fieldName}-${option.value}`
          return (
            <label key={option.value} className="likert-option" htmlFor={id}>
              <input
                id={id}
                type="radio"
                name={fieldName}
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
              />
              <span className="likert-number">{option.value}</span>
              {option.label !== option.value ? <span className="visually-hidden"> {option.label}</span> : null}
            </label>
          )
        })}
      </div>
      {first && last ? (
        <div className="likert-ends">
          <span>{first.label}</span>
          <span>{last.label}</span>
        </div>
      ) : null}
      {error ? (
        <p id={errorId} className="field-error" role="alert">
          {error}
        </p>
      ) : null}
    </fieldset>
  )
}
