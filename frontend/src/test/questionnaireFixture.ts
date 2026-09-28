import type { Question, Questionnaire } from '../types/questionnaire'

function likertOptions(min: number, max: number, low: string, high: string) {
  return Array.from({ length: max - min + 1 }, (_, index) => {
    const value = String(min + index)
    const label = index === 0 ? low : index === max - min ? high : value
    return { value, label, onet_element_id: null, sort_order: index }
  })
}

const level: Question = {
  code: 'level',
  section: 'profile',
  prompt: 'What is your current undergraduate level?',
  response_type: 'choice',
  block: 'profile',
  onet_element_id: null,
  onet_scale_id: null,
  sort_order: 10,
  is_required: true,
  min_value: null,
  max_value: null,
  min_selections: null,
  max_selections: null,
  options: [
    { value: '100', label: '100 level', onet_element_id: null, sort_order: 0 },
    { value: '200', label: '200 level', onet_element_id: null, sort_order: 1 },
    { value: '300', label: '300 level', onet_element_id: null, sort_order: 2 },
  ],
}

const department: Question = {
  code: 'department',
  section: 'profile',
  prompt: 'Department / programme (optional). Leave blank if not confirmed.',
  response_type: 'text',
  block: 'profile',
  onet_element_id: null,
  onet_scale_id: null,
  sort_order: 20,
  is_required: false,
  min_value: null,
  max_value: null,
  min_selections: null,
  max_selections: null,
  options: [],
}

const interest: Question = {
  code: 'interest_realistic',
  section: 'riasec',
  prompt: 'How much would you enjoy realistic work?',
  response_type: 'likert',
  block: 'riasec',
  onet_element_id: '1.B.1.a',
  onet_scale_id: 'OI',
  sort_order: 30,
  is_required: true,
  min_value: 1,
  max_value: 7,
  min_selections: null,
  max_selections: null,
  options: likertOptions(1, 7, 'Strongly dislike this type of work', 'Strongly like this type of work'),
}

const sia: Question = {
  code: 'sia',
  section: 'sia',
  prompt: 'Select 1 to 5 specific interest areas, then rate how much you would enjoy each (1–7).',
  response_type: 'sparse_select',
  block: 'sia',
  onet_element_id: null,
  onet_scale_id: 'OI',
  sort_order: 40,
  is_required: true,
  min_value: 1,
  max_value: 7,
  min_selections: 1,
  max_selections: 5,
  options: [
    { value: '1.B.3.a', label: 'Mechanics', onet_element_id: '1.B.3.a', sort_order: 0 },
    { value: '1.B.3.b', label: 'Computers', onet_element_id: '1.B.3.b', sort_order: 1 },
    { value: '1.B.3.c', label: 'Visual Arts', onet_element_id: '1.B.3.c', sort_order: 2 },
    { value: '1.B.3.d', label: 'Teaching', onet_element_id: '1.B.3.d', sort_order: 3 },
    { value: '1.B.3.e', label: 'Sales', onet_element_id: '1.B.3.e', sort_order: 4 },
    { value: '1.B.3.f', label: 'Accounting', onet_element_id: '1.B.3.f', sort_order: 5 },
  ],
}

const knowledge: Question = {
  code: 'knowledge',
  section: 'knowledge',
  prompt: 'Select 1 to 5 knowledge areas you are strongest in, then rate each (1–5).',
  response_type: 'sparse_select',
  block: 'knowledge',
  onet_element_id: null,
  onet_scale_id: 'IM',
  sort_order: 50,
  is_required: true,
  min_value: 1,
  max_value: 5,
  min_selections: 1,
  max_selections: 5,
  options: [
    { value: '2.C.1.a', label: 'Administration', onet_element_id: '2.C.1.a', sort_order: 0 },
    { value: '2.C.3.a', label: 'Computers and Electronics', onet_element_id: '2.C.3.a', sort_order: 1 },
    { value: '2.C.4.a', label: 'Mathematics', onet_element_id: '2.C.4.a', sort_order: 2 },
    { value: '2.C.4.b', label: 'Physics', onet_element_id: '2.C.4.b', sort_order: 3 },
    { value: '2.C.4.e', label: 'Psychology', onet_element_id: '2.C.4.e', sort_order: 4 },
    { value: '2.C.7.a', label: 'English Language', onet_element_id: '2.C.7.a', sort_order: 5 },
  ],
}

const preference: Question = {
  code: 'pref_indoor',
  section: 'work_preferences',
  prompt: 'I prefer indoor work.',
  response_type: 'preference',
  block: 'work_context',
  onet_element_id: '4.C.2.a.1.a',
  onet_scale_id: 'CX',
  sort_order: 60,
  is_required: true,
  min_value: 1,
  max_value: 5,
  min_selections: null,
  max_selections: null,
  options: likertOptions(1, 5, 'Strongly disagree', 'Strongly agree'),
}

export const mockQuestionnaire: Questionnaire = {
  version: 'questionnaire_v1',
  feature_version: 'onet_30_3_v1',
  status: 'published',
  questions: [level, department, interest, sia, knowledge, preference],
}

export const mockSubmitConfirmation = {
  id: '22222222-2222-2222-2222-222222222222',
  assessment_id: '33333333-3333-3333-3333-333333333333',
  created_at: '2026-08-24T00:00:00Z',
  questionnaire_version: 'questionnaire_v1',
  feature_version: 'onet_30_3_v1',
  config_version: 'config_v1',
  k: 10,
  items: [{ rank: 1 }],
}
