export const EXPERIENCE_SCALE = [
  { value: 1, label: 'Strongly Disagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly Agree' },
] as const

export const EXPERIENCE_SCALE_ITEMS = [
  {
    field: 'questions_easy_to_understand',
    prompt: 'The assessment questions were easy to understand.',
  },
  {
    field: 'assessment_easy_to_complete',
    prompt: 'The assessment was easy to complete.',
  },
  {
    field: 'system_easy_to_navigate',
    prompt: 'The system was easy to navigate.',
  },
  {
    field: 'recommendations_easy_to_understand',
    prompt: 'The career recommendations were easy to understand.',
  },
  {
    field: 'explanations_helped',
    prompt: 'The explanations helped me understand why the careers were recommended.',
  },
  {
    field: 'reflected_interests',
    prompt: 'The recommendations reflected my interests.',
  },
  {
    field: 'reflected_skills',
    prompt: 'The recommendations reflected my skills.',
  },
  {
    field: 'helped_explore_options',
    prompt: 'The system helped me explore career options.',
  },
  {
    field: 'would_use_again',
    prompt: 'I would use this system again for career exploration.',
  },
  {
    field: 'would_discuss_with_counsellor',
    prompt: 'I would discuss the recommendations with a career counsellor.',
  },
] as const

export type ExperienceScaleField = (typeof EXPERIENCE_SCALE_ITEMS)[number]['field']

export type ExperienceEvaluationAnswers = Record<ExperienceScaleField, number | null> & {
  liked_most_and_improvement: string
}

export const EMPTY_EXPERIENCE_ANSWERS: ExperienceEvaluationAnswers = {
  questions_easy_to_understand: null,
  assessment_easy_to_complete: null,
  system_easy_to_navigate: null,
  recommendations_easy_to_understand: null,
  explanations_helped: null,
  reflected_interests: null,
  reflected_skills: null,
  helped_explore_options: null,
  would_use_again: null,
  would_discuss_with_counsellor: null,
  liked_most_and_improvement: '',
}

export function missingExperienceFields(answers: ExperienceEvaluationAnswers): ExperienceScaleField[] {
  return EXPERIENCE_SCALE_ITEMS.filter((item) => answers[item.field] == null).map((item) => item.field)
}

export function experienceEvaluationLoadError(error: { status?: number; code?: string; message?: string }): string {
  if (error.status === 401 || error.code === 'unauthenticated') {
    return 'Your session has expired. Please log in again to evaluate your experience.'
  }
  if (error.status === 403 || error.code === 'forbidden') {
    return "You cannot evaluate another student's recommendation run."
  }
  if (error.status === 404 || error.code === 'invalid_recommendation_run') {
    return 'This recommendation run was not found.'
  }
  return error.message || 'The experience evaluation could not be loaded.'
}

export function experienceEvaluationSubmitError(error: { status?: number; code?: string; message?: string }): string {
  if (error.status === 409 || error.code === 'experience_evaluation_exists') {
    return 'You have already submitted an experience evaluation for this recommendation run.'
  }
  if (error.status === 422) {
    return 'Please answer every scaled question using 1 (Strongly Disagree) to 5 (Strongly Agree).'
  }
  return experienceEvaluationLoadError(error)
}
