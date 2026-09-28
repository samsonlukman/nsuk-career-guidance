import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { submitAssessment } from '../api/assessments'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert } from '../components/Alert'
import { ProgressIndicator } from '../components/assessment/ProgressIndicator'
import { QuestionRenderer } from '../components/assessment/QuestionRenderer'
import { ReviewScreen } from '../components/assessment/ReviewScreen'
import { Button, ButtonLink } from '../components/Button'
import { Spinner } from '../components/Spinner'
import { useAssessment } from '../hooks/useAssessment'
import { clearAssessmentDraft, incompleteQuestions, submissionErrorMessage, toSubmissionPayload, validateQuestion } from '../utils/assessmentAnswers'
import { questionsInSection, sectionTitle, sectionsInOrder } from '../utils/questionnaire'

export function AssessmentPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const assessment = useAssessment(user!)
  const [stepError, setStepError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const { questions, stepIndex } = assessment
  const onReview = stepIndex >= questions.length && questions.length > 0
  const current = onReview ? null : questions[stepIndex]
  const sections = useMemo(() => sectionsInOrder(questions), [questions])

  const sectionMeta = useMemo(() => {
    if (!current) {
      return {
        section: 'review',
        sectionIndex: sections.length,
        sectionCount: sections.length,
        questionInSection: 1,
        questionsInSection: 1,
      }
    }
    const inSection = questionsInSection(questions, current.section)
    return {
      section: current.section,
      sectionIndex: sections.indexOf(current.section) + 1,
      sectionCount: sections.length,
      questionInSection: inSection.findIndex((item) => item.code === current.code) + 1,
      questionsInSection: inSection.length,
    }
  }, [current, questions, sections])

  if (!user) {
    return <Alert>Your session could not be loaded.</Alert>
  }

  if (assessment.loading) {
    return <Spinner label="Loading the questionnaire" />
  }

  if (assessment.loadError || !assessment.questionnaire) {
    return (
      <article className="assessment-page">
        <Alert>{assessment.loadError ?? 'The questionnaire could not be loaded.'}</Alert>
        <Button onClick={() => assessment.reload()}>Try again</Button>
      </article>
    )
  }

  function goBack() {
    setStepError(null)
    setSubmitError(null)
    assessment.setStepIndex((index) => Math.max(0, index - 1))
  }

  function goContinue() {
    if (!current) return
    const error = validateQuestion(current, assessment.answers[current.code])
    if (error) {
      setStepError(error)
      return
    }
    setStepError(null)
    assessment.setStepIndex((index) => index + 1)
  }

  async function handleSubmit() {
    if (submitting || !assessment.questionnaire) return
    const blocking = incompleteQuestions(questions, assessment.answers)
    if (blocking.length > 0) {
      setSubmitError('Complete the highlighted questions before submitting.')
      return
    }
    setSubmitError(null)
    setSubmitting(true)
    try {
      const confirmation = await submitAssessment(
        toSubmissionPayload(assessment.questionnaire.version, questions, assessment.answers),
      )
      clearAssessmentDraft(user.id)
      navigate('/assessment/complete', { replace: true, state: confirmation })
    } catch (err) {
      const apiError = err instanceof ApiError ? err : { message: 'The assessment could not be submitted.' }
      setSubmitError(submissionErrorMessage(apiError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="assessment-page">
      <header className="page-header">
        <p className="eyebrow">Career assessment</p>
        <h1>{onReview ? 'Review and submit' : sectionTitle(sectionMeta.section)}</h1>
        <p className="lede">
          Answer one step at a time. Your responses are saved on this device until you submit.
          Recommendations are calculated only after you submit.
        </p>
      </header>

      <ProgressIndicator
        section={sectionMeta.section}
        sectionIndex={sectionMeta.sectionIndex}
        sectionCount={sectionMeta.sectionCount}
        questionInSection={sectionMeta.questionInSection}
        questionsInSection={sectionMeta.questionsInSection}
        overallIndex={onReview ? questions.length : stepIndex}
        overallTotal={questions.length}
        onReview={onReview}
      />

      <p className="assessment-save-status" aria-live="polite">
        {assessment.savedAt
          ? 'Answers saved on this device. They have not been submitted yet.'
          : 'Answers will be saved on this device as you go.'}
      </p>

      {onReview ? (
        <ReviewScreen
          questionnaireVersion={assessment.questionnaire.version}
          featureVersion={assessment.questionnaire.feature_version}
          questions={questions}
          answers={assessment.answers}
          onEdit={(index) => {
            setSubmitError(null)
            assessment.setStepIndex(index)
          }}
        />
      ) : current ? (
        <QuestionRenderer
          question={current}
          answer={assessment.answers[current.code]}
          error={stepError ?? undefined}
          onChange={(answer) => {
            setStepError(null)
            assessment.setAnswer(current.code, answer)
          }}
        />
      ) : null}

      {submitError ? <Alert>{submitError}</Alert> : null}
      {submitError?.includes('session has expired') ? (
        <p>
          <Link to="/login">Return to log in</Link>
        </p>
      ) : null}

      {onReview ? (
        <p className="assessment-warning" role="note">
          Submitting will generate personalized recommendations from your answers and official
          occupational information. This does not predict job success or guarantee employment.
        </p>
      ) : null}

      <div className="assessment-nav">
        <Button variant="secondary" onClick={goBack} disabled={stepIndex === 0 || submitting}>
          Back
        </Button>
        {onReview ? (
          <Button onClick={() => void handleSubmit()} disabled={submitting}>
            {submitting ? 'Submitting assessment…' : 'Submit Assessment'}
          </Button>
        ) : (
          <Button onClick={goContinue}>Continue</Button>
        )}
      </div>
      <p className="form-foot">
        <ButtonLink to="/dashboard" variant="ghost">
          Return to dashboard
        </ButtonLink>
      </p>
    </article>
  )
}
