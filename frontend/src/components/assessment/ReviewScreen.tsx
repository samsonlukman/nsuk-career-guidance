import type { AnswerMap, Question } from '../../types/questionnaire'
import { incompleteQuestions, summarizeAnswer } from '../../utils/assessmentAnswers'
import { questionsInSection, sectionTitle, sectionsInOrder } from '../../utils/questionnaire'
import { Alert } from '../Alert'

type ReviewScreenProps = {
  questions: Question[]
  answers: AnswerMap
  onEdit: (index: number) => void
}

export function ReviewScreen({
  questions,
  answers,
  onEdit,
}: ReviewScreenProps) {
  const incomplete = incompleteQuestions(questions, answers)
  const sections = sectionsInOrder(questions)

  return (
    <div className="review-screen">
      <p className="lede">
        Check your answers before submitting. After you submit, you will receive personalised
        career recommendations based on this assessment.
      </p>

      {incomplete.length > 0 ? (
        <Alert>
          {incomplete.length === 1
            ? '1 question still needs a valid answer.'
            : `${incomplete.length} questions still need a valid answer.`}
        </Alert>
      ) : (
        <Alert tone="info">All required questions have an answer. You can still edit any section.</Alert>
      )}

      {sections.map((section) => {
        const items = questionsInSection(questions, section)
        return (
          <section key={section} className="review-section" aria-labelledby={`review-${section}`}>
            <h2 id={`review-${section}`}>{sectionTitle(section)}</h2>
            <ul className="review-list">
              {items.map((question) => {
                const index = questions.findIndex((item) => item.code === question.code)
                const issue = incomplete.some((item) => item.code === question.code)
                return (
                  <li key={question.code}>
                    <div>
                      <p className="review-prompt">{question.prompt}</p>
                      <p className={issue ? 'review-answer review-missing' : 'review-answer'}>
                        {summarizeAnswer(question, answers[question.code])}
                      </p>
                    </div>
                    <button type="button" className="btn btn-ghost" onClick={() => onEdit(index)}>
                      Edit
                    </button>
                  </li>
                )
              })}
            </ul>
          </section>
        )
      })}
    </div>
  )
}
