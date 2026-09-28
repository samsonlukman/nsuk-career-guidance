import type { Question, QuestionAnswer, SparseAnswer } from '../../types/questionnaire'
import { ChoiceQuestion } from './ChoiceQuestion'
import { RatingQuestion } from './RatingQuestion'
import { SparseSelectQuestion } from './SparseSelectQuestion'
import { TextQuestion } from './TextQuestion'

type QuestionRendererProps = {
  question: Question
  answer: QuestionAnswer | undefined
  error?: string
  onChange: (answer: QuestionAnswer) => void
}

export function QuestionRenderer({ question, answer, error, onChange }: QuestionRendererProps) {
  if (question.response_type === 'text') {
    return (
      <TextQuestion
        question={question}
        value={answer?.kind === 'value' ? answer.value : ''}
        error={error}
        onChange={(value) => onChange({ kind: 'value', value })}
      />
    )
  }

  if (question.response_type === 'choice') {
    return (
      <ChoiceQuestion
        question={question}
        value={answer?.kind === 'value' ? answer.value : ''}
        error={error}
        onChange={(value) => onChange({ kind: 'value', value })}
      />
    )
  }

  if (question.response_type === 'likert' || question.response_type === 'preference') {
    return (
      <RatingQuestion
        question={question}
        value={answer?.kind === 'value' ? answer.value : ''}
        error={error}
        onChange={(value) => onChange({ kind: 'value', value })}
      />
    )
  }

  if (question.response_type === 'sparse_select') {
    const sparse: SparseAnswer | undefined = answer?.kind === 'selections' ? answer : undefined
    return (
      <SparseSelectQuestion
        question={question}
        answer={sparse}
        error={error}
        onChange={onChange}
      />
    )
  }

  return (
    <p role="alert" className="field-error">
      This question type ({question.response_type}) is not supported by the website yet.
    </p>
  )
}
