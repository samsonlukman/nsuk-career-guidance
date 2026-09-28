import type { Question, SparseAnswer } from '../../types/questionnaire'
import { canSelectAnother, rateSparseSelection, toggleSparseSelection } from '../../utils/assessmentAnswers'
import { optionLabel, sortedOptions } from '../../utils/questionnaire'
import { RatingQuestion } from './RatingQuestion'

type SparseSelectQuestionProps = {
  question: Question
  answer: SparseAnswer | undefined
  error?: string
  onChange: (answer: SparseAnswer) => void
}

export function SparseSelectQuestion({ question, answer, error, onChange }: SparseSelectQuestionProps) {
  const options = sortedOptions(question)
  const selected = answer?.selections ?? []
  const selectedIds = new Set(selected.map((item) => item.element_id))
  const atLimit = !canSelectAnother(question, answer)
  const errorId = `${question.code}-error`
  const min = question.min_selections
  const max = question.max_selections

  return (
    <div className="sparse-question">
      <fieldset className="question-fieldset" aria-describedby={error ? errorId : undefined}>
        <legend>{question.prompt}</legend>
        <p className="field-hint">
          {min != null && max != null
            ? `Select ${min} to ${max} areas from the official list, then rate each selected area. Unselected areas are not sent.`
            : 'Select the areas that apply, then rate each selected area.'}
        </p>
        <p className="status-label">
          {selected.length} selected
          {max != null ? ` (maximum ${max})` : ''}
        </p>
        <ul className="sparse-options">
          {options.map((option) => {
            const id = `${question.code}-${option.value}`
            const checked = selectedIds.has(option.value)
            const disabled = !checked && atLimit
            return (
              <li key={option.value}>
                <label className="choice-option" htmlFor={id}>
                  <input
                    id={id}
                    type="checkbox"
                    name={question.code}
                    value={option.value}
                    checked={checked}
                    disabled={disabled}
                    onChange={() => onChange(toggleSparseSelection(question, answer, option.value))}
                  />
                  <span>{option.label}</span>
                  {disabled ? <span className="visually-hidden"> Selection limit reached</span> : null}
                </label>
              </li>
            )
          })}
        </ul>
      </fieldset>

      {selected.length > 0 ? (
        <div className="sparse-ratings" aria-label="Ratings for selected areas">
          <h3>Selected areas</h3>
          {selected.map((item) => {
            const ratingQuestion: Question = {
              ...question,
              code: `${question.code}-${item.element_id}`,
              prompt: `How would you rate ${optionLabel(question, item.element_id)}?`,
            }
            return (
              <RatingQuestion
                key={item.element_id}
                question={ratingQuestion}
                name={`${question.code}-${item.element_id}`}
                legend={`Rate ${optionLabel(question, item.element_id)}`}
                value={item.value == null ? '' : String(item.value)}
                onChange={(value) => onChange(rateSparseSelection(answer, item.element_id, Number(value)))}
              />
            )
          })}
        </div>
      ) : null}

      {error ? (
        <p id={errorId} className="field-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
