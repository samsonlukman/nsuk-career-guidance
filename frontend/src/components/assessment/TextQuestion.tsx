import type { Question } from '../../types/questionnaire'

type TextQuestionProps = {
  question: Question
  value: string
  error?: string
  onChange: (value: string) => void
}

export function TextQuestion({ question, value, error, onChange }: TextQuestionProps) {
  const errorId = `${question.code}-error`
  const hintId = `${question.code}-hint`
  return (
    <div className="field">
      <label htmlFor={question.code}>{question.prompt}</label>
      {!question.is_required ? (
        <p id={hintId} className="field-hint">
          Optional.
        </p>
      ) : null}
      <input
        id={question.code}
        name={question.code}
        type="text"
        value={value}
        required={question.is_required}
        aria-invalid={error ? true : undefined}
        aria-describedby={[!question.is_required ? hintId : null, error ? errorId : null].filter(Boolean).join(' ') || undefined}
        onChange={(event) => onChange(event.target.value)}
      />
      {error ? (
        <p id={errorId} className="field-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
