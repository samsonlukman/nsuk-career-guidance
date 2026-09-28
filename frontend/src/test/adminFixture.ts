import type {
  AdminDashboard,
  AdminOnetSnapshot,
  AdminQuestionnaire,
  AdminRatingList,
  AdminRecommendationConfig,
  AdminRunDetail,
  AdminRunList,
  AdminStudentDetail,
  AdminStudentList,
  FacultyKnowledgeCatalog,
  FacultyKnowledgePrior,
  FacultyKnowledgePriorAuditList,
  FacultyKnowledgePriorList,
} from '../types/admin'
import { adminUser, studentUser } from './helpers'
import { mockRecommendationRun, RUN_ID } from './recommendationFixture'

export const mockAdminDashboard: AdminDashboard = {
  students_total: 12,
  assessments_completed: 4,
  recommendation_runs: 3,
  ratings_total: 2,
  ratings_average: 4.0,
  active_onet: {
    snapshot_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    onet_release: '30.3',
    onet_release_month: 'May 2026',
    feature_version: 'onet_30_3_v1',
    occupation_count: 923,
    recommendable_count: 400,
    knn_feature_count: 80,
  },
  active_questionnaire: {
    version: 'questionnaire_v1',
    status: 'published',
    feature_version: 'onet_30_3_v1',
    question_count: 40,
    option_count: 90,
  },
  active_config: {
    version: 'config_v1',
    k: 10,
    metric: 'weighted_block_cosine',
    feature_version: 'onet_30_3_v1',
    block_weights: { riasec: 0.25, knowledge: 0.1 },
  },
  system: {
    api: 'ok',
    database: 'connected',
    active_onet_snapshot: true,
    active_questionnaire: true,
    active_recommendation_config: true,
  },
  notes: [
    'Counts are taken from stored records. Nothing here is estimated.',
    'Ratings are user relevance feedback, not a measure of recommendation accuracy.',
  ],
}

export const mockStudentList: AdminStudentList = {
  page: 1,
  page_size: 20,
  total: 1,
  total_pages: 1,
  items: [
    {
      id: studentUser.id,
      email: studentUser.email,
      is_active: true,
      created_at: '2026-08-20T10:00:00Z',
      last_login_at: '2026-08-24T00:10:00Z',
      first_name: 'Amina',
      last_name: 'Bello',
      matric_number: 'NSU/2021/001',
      faculty: 'Natural and Applied Sciences',
      department: 'Computer Science',
      level: '400',
      latest_assessment_status: 'completed',
      latest_assessment_completed_at: '2026-08-24T00:39:00Z',
      recommendation_run_count: 1,
    },
  ],
}

export const mockStudentDetail: AdminStudentDetail = {
  id: studentUser.id,
  email: studentUser.email,
  is_active: true,
  created_at: '2026-08-20T10:00:00Z',
  last_login_at: '2026-08-24T00:10:00Z',
  profile: {
    first_name: 'Amina',
    last_name: 'Bello',
    matric_number: 'NSU/2021/001',
    faculty: 'Natural and Applied Sciences',
    department: 'Computer Science',
    level: '400',
    further_study: 'maybe',
    course_relatedness: 'open',
  },
  assessments: [
    {
      id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
      status: 'completed',
      questionnaire_version: 'questionnaire_v1',
      feature_version: 'onet_30_3_v1',
      started_at: '2026-08-24T00:20:00Z',
      completed_at: '2026-08-24T00:39:00Z',
    },
  ],
  recommendation_history: [
    {
      run_id: RUN_ID,
      created_at: '2026-08-24T00:39:00Z',
      k: 10,
      feature_version: 'onet_30_3_v1',
      questionnaire_version: 'questionnaire_v1',
      config_version: 'config_v1',
      onet_release: '30.3',
      eligible_count: 400,
      item_count: 10,
      top_occupation_title: 'Computer Science Teachers, Postsecondary',
      top_onetsoc_code: '25-1021.00',
    },
  ],
}

export const mockRunList: AdminRunList = {
  page: 1,
  page_size: 20,
  total: 1,
  total_pages: 1,
  items: [
    {
      run_id: RUN_ID,
      student_id: studentUser.id,
      student_email: studentUser.email,
      student_name: 'Amina Bello',
      assessment_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
      assessment_completed_at: '2026-08-24T00:39:00Z',
      created_at: '2026-08-24T00:39:00Z',
      onet_release: '30.3',
      questionnaire_version: 'questionnaire_v1',
      config_version: 'config_v1',
      feature_version: 'onet_30_3_v1',
      item_count: 10,
      top_occupation_title: 'Computer Science Teachers, Postsecondary',
      top_onetsoc_code: '25-1021.00',
    },
  ],
}

export const mockAdminRunDetail: AdminRunDetail = {
  student: {
    id: studentUser.id,
    email: studentUser.email,
    first_name: 'Amina',
    last_name: 'Bello',
  },
  run: mockRecommendationRun,
}

export const mockRatingList: AdminRatingList = {
  page: 1,
  page_size: 20,
  total: 1,
  total_pages: 1,
  items: [
    {
      id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
      relevance_1_to_5: 4,
      comment: 'Useful as a discussion prompt',
      created_at: '2026-08-24T00:45:00Z',
      occupation_title: 'Computer Science Teachers, Postsecondary',
      onetsoc_code: '25-1021.00',
      run_id: RUN_ID,
      student_id: studentUser.id,
      student_email: studentUser.email,
    },
  ],
  summary: {
    ratings_total: 1,
    average_relevance: 4,
    distribution: { 1: 0, 2: 0, 3: 0, 4: 1, 5: 0 },
    note: 'These values are user relevance feedback for later evaluation. They are not a measure of recommendation accuracy.',
  },
}

export const mockOnetSnapshot: AdminOnetSnapshot = {
  snapshot_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
  onet_release: '30.3',
  onet_release_month: 'May 2026',
  feature_version: 'onet_30_3_v1',
  occupation_count: 923,
  recommendable_count: 400,
  knn_feature_count: 80,
  job_zones: [
    {
      job_zone: 5,
      name: 'Job Zone Five: Extensive Preparation Needed',
      education: 'Most of these occupations require graduate school.',
      occupation_count: 146,
      recommendable_count: 120,
    },
  ],
  note: 'O*NET remains the authoritative occupational source. This view is read-only.',
}

export const mockQuestionnaire: AdminQuestionnaire = {
  version: 'questionnaire_v1',
  status: 'published',
  feature_version: 'onet_30_3_v1',
  question_count: 1,
  option_count: 33,
  questions: [
    {
      code: 'knowledge',
      section: 'knowledge',
      prompt: 'Select knowledge areas you are strongest in.',
      response_type: 'sparse_select',
      block: 'knowledge',
      onet_element_id: null,
      sort_order: 1,
      is_required: true,
      option_count: 33,
    },
  ],
  note: 'Questionnaire inspection only. Editing is not available from this view.',
}

export const mockConfig: AdminRecommendationConfig = {
  version: 'config_v1',
  k: 10,
  metric: 'weighted_block_cosine',
  feature_version: 'onet_30_3_v1',
  block_weights: { riasec: 0.25, knowledge: 0.1 },
  note: 'Read-only. Changing k, metric, or weights from this interface is not allowed.',
}

export const mockCatalog: FacultyKnowledgeCatalog = {
  faculties: ['Engineering', 'Natural and Applied Sciences'],
  knowledge_elements: [
    { element_id: '2.C.3.a', element_name: 'Computers and Electronics' },
    { element_id: '2.C.4.a', element_name: 'Mathematics' },
  ],
  note: 'Faculty names are official NSUK faculties. Knowledge element IDs come from the active O*NET snapshot.',
}

export const mockPrior: FacultyKnowledgePrior = {
  id: 7,
  faculty: 'Natural and Applied Sciences',
  element_id: '2.C.3.a',
  element_name: 'Computers and Electronics',
  created_by: adminUser.id,
  created_at: '2026-08-24T01:00:00Z',
  updated_at: '2026-08-24T01:00:00Z',
}

export const mockPriorList = (items: FacultyKnowledgePrior[] = []): FacultyKnowledgePriorList => ({ items })

export const mockAuditList: FacultyKnowledgePriorAuditList = {
  page: 1,
  page_size: 20,
  total: 1,
  total_pages: 1,
  items: [
    {
      id: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
      prior_id: 7,
      action: 'create',
      faculty: 'Natural and Applied Sciences',
      element_id: '2.C.3.a',
      element_name: 'Computers and Electronics',
      previous_faculty: null,
      previous_element_id: null,
      previous_element_name: null,
      actor_user_id: adminUser.id,
      actor_email: adminUser.email,
      created_at: '2026-08-24T01:00:00Z',
    },
  ],
}
