import type { AnswerMap, Question } from '../../types/questionnaire'
import { incompleteQuestions, summarizeAnswer } from '../../utils/assessmentAnswers'
import { questionsInSection, sectionTitle, sectionsInOrder } from '../../utils/questionnaire'
import { Alert } from '../Alert'

type ReviewScreenProps = {
  questionnaireVersion: string
  featureVersion: string
  questions: Question[]
  answers: AnswerMap
  onEdit: (index: number) => void
}

export function ReviewScreen({
  questionnaireVersion,
  featureVersion,
  questions,
  answers,
  onEdit,
}: ReviewScreenProps) {
  const incomplete = incompleteQuestions(questions, answers)
  const sections = sectionsInOrder(questions)

  return (
    <div className="review-screen">
      <p className="lede">
        Check your answers before submitting. Submitting sends them to the server, which will
        generate personalized recommendations. Scoring happens on the server, not in this page.
      </p>
      <dl className="meta-list">
        <div>
          <dt>Questionnaire</dt>
          <dd>{questionnaireVersion}</dd>
        </div>
        <div>
          <dt>Feature version</dt>
          <dd>{featureVersion}</dd>
        </div>
      </dl>

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
