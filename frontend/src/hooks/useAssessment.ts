import { useCallback, useEffect, useMemo, useState } from 'react'

import { fetchActiveQuestionnaire } from '../api/questionnaires'
import { ApiError } from '../api/client'
import type { CurrentUser } from '../types/auth'
import type { AnswerMap, QuestionAnswer, Questionnaire } from '../types/questionnaire'
import {
  loadAssessmentDraft,
  saveAssessmentDraft,
  type AssessmentDraft,
} from '../utils/assessmentAnswers'
import { orderedQuestions, prefillFromProfile } from '../utils/questionnaire'

export function useAssessment(user: CurrentUser) {
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [answers, setAnswers] = useState<AnswerMap>({})
  const [stepIndex, setStepIndex] = useState(0)
  const [savedAt, setSavedAt] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setLoadError(null)
    fetchActiveQuestionnaire()
      .then((data) => {
        if (cancelled) return
        const questions = orderedQuestions(data)
        const draft = loadAssessmentDraft(user.id, data.version)
        setQuestionnaire(data)
        if (draft) {
          setAnswers(draft.answers)
          setStepIndex(Math.min(Math.max(draft.stepIndex, 0), questions.length))
          setSavedAt(draft.updatedAt)
        } else {
          setAnswers(prefillFromProfile(questions, user))
          setStepIndex(0)
          setSavedAt(null)
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          setLoadError('Your session has expired. Please log in again.')
        } else if (err instanceof ApiError) {
          setLoadError(err.message)
        } else {
          setLoadError('Unable to load the questionnaire.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [user, reloadToken])

  const questions = useMemo(() => (questionnaire ? orderedQuestions(questionnaire) : []), [questionnaire])

  useEffect(() => {
    if (!questionnaire) return
    const draft: AssessmentDraft = {
      questionnaireVersion: questionnaire.version,
      stepIndex,
      answers,
      updatedAt: new Date().toISOString(),
    }
    saveAssessmentDraft(user.id, draft)
    setSavedAt(draft.updatedAt)
  }, [answers, questionnaire, stepIndex, user.id])

  const setAnswer = useCallback((code: string, answer: QuestionAnswer) => {
    setAnswers((current) => ({ ...current, [code]: answer }))
  }, [])

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1)
  }, [])

  return {
    questionnaire,
    questions,
    loading,
    loadError,
    answers,
    setAnswer,
    stepIndex,
    setStepIndex,
    savedAt,
    reload,
  }
}
