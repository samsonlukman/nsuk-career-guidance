import type { Question } from '../../types/questionnaire'
import { sortedOptions } from '../../utils/questionnaire'

type ChoiceQuestionProps = {
  question: Question
  value: string
  error?: string
  onChange: (value: string) => void
}

export function ChoiceQuestion({ question, value, error, onChange }: ChoiceQuestionProps) {
  const options = sortedOptions(question)
  const errorId = `${question.code}-error`
  const useSelect = options.length > 6

  if (useSelect) {
    return (
      <div className="field">
        <label htmlFor={question.code}>{question.prompt}</label>
        <select
          id={question.code}
          name={question.code}
          value={value}
          required={question.is_required}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Select an option</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error ? (
          <p id={errorId} className="field-error" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    )
  }

  return (
    <fieldset className="question-fieldset" aria-describedby={error ? errorId : undefined}>
      <legend>{question.prompt}</legend>
      <div className="choice-list">
        {options.map((option) => {
          const id = `${question.code}-${option.value}`
          return (
            <label key={option.value} className="choice-option" htmlFor={id}>
              <input
                id={id}
                type="radio"
                name={question.code}
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
              />
              <span>{option.label}</span>
            </label>
          )
        })}
      </div>
      {error ? (
        <p id={errorId} className="field-error" role="alert">
          {error}
        </p>
      ) : null}
    </fieldset>
  )
}
