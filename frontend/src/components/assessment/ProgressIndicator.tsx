import { sectionTitle } from '../../utils/questionnaire'

type ProgressIndicatorProps = {
  section: string
  sectionIndex: number
  sectionCount: number
  questionInSection: number
  questionsInSection: number
  overallIndex: number
  overallTotal: number
  onReview: boolean
}

export function ProgressIndicator({
  section,
  sectionIndex,
  sectionCount,
  questionInSection,
  questionsInSection,
  overallIndex,
  overallTotal,
  onReview,
}: ProgressIndicatorProps) {
  const percent = onReview ? 100 : Math.round((overallIndex / overallTotal) * 100)
  const label = onReview
    ? 'Review your answers before submitting'
    : `Section ${sectionIndex} of ${sectionCount}: ${sectionTitle(section)}. Question ${questionInSection} of ${questionsInSection}. ${overallIndex} of ${overallTotal} questions completed.`

  return (
    <div className="assessment-progress">
      <div className="assessment-progress-meta">
        {onReview ? (
          <p className="eyebrow">Review</p>
        ) : (
          <p className="eyebrow">
            Section {sectionIndex} of {sectionCount} · {sectionTitle(section)}
          </p>
        )}
        <p className="assessment-progress-step">
          {onReview
            ? 'Final check'
            : `Question ${questionInSection} of ${questionsInSection} in this section`}
        </p>
      </div>
      <div
        className="progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={overallTotal}
        aria-valuenow={onReview ? overallTotal : overallIndex + 1}
        aria-valuetext={label}
        aria-label="Assessment progress"
      >
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <p className="assessment-progress-overall">
        {onReview
          ? `${overallTotal} of ${overallTotal} questions`
          : `Question ${overallIndex + 1} of ${overallTotal}`}
      </p>
    </div>
  )
}
