import type { Dashboard } from '../types/api'
import type { OccupationDetail, RatingOut, RecommendationRun } from '../types/recommendations'
import { studentUser } from './helpers'

export const RUN_ID = '8b03250e-0f6d-4444-9d28-11813c738e23'
export const TOP_ITEM_ID = '0c797d21-7e24-4eae-b664-07614f18c09e'
export const MID_ITEM_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2'
export const FLAG_ITEM_ID = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb3'

export const mockRecommendationRun: RecommendationRun = {
  id: RUN_ID,
  assessment_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
  created_at: '2026-08-24T00:39:00Z',
  k: 10,
  metric: 'weighted_block_cosine',
  eligible_count: 400,
  elapsed_ms: 120,
  feature_version: 'onet_30_3_v1',
  onet_release: '30.3',
  onet_snapshot_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
  questionnaire_version: 'questionnaire_v1',
  config_version: 'config_v1',
  block_weights: {
    riasec: 0.25,
    sia: 0.2,
    essential_skills: 0.2,
    transferable_skills: 0.15,
    work_styles: 0.1,
    knowledge: 0.1,
  },
  notes: ['Scores are O*NET profile similarity, not predicted job success or accuracy.'],
  items: [
    {
      id: FLAG_ITEM_ID,
      rank: 3,
      onetsoc_code: '29-1031.00',
      title: 'Dietitians and Nutritionists',
      job_zone: 5,
      distance: 0.173,
      raw_similarity: 0.827,
      recommendation_score: 0.744,
      explanation:
        'Dietitians and Nutritionists was recommended because your profile aligns on Professional Advising. Match scores are similarity, not predicted success.',
      job_zone_note: 'Most of these occupations require graduate school.',
      work_activities: ['Assisting and Caring for Others'],
      contributing_features: [
        {
          block: 'sia',
          element_id: '1.B.3.ad',
          element_name: 'Professional Advising',
          student_raw: 7,
          student_normalized: 1,
          occupation_raw: 4.5,
          occupation_normalized: 0.6,
          note: 'Selected area is also important in this occupation',
        },
      ],
      rule_flags: [
        {
          rule_code: 'R-ZONE-5',
          action: 'flag',
          reason: 'Job Zone 5 typically requires graduate or professional training',
          penalty: null,
          element_id: null,
          domain: null,
        },
      ],
      penalties: [
        {
          rule_code: 'R-CONTEXT',
          action: 'penalise',
          reason: 'Work setting mismatch: occupation has high public/customer contact',
          penalty: 0.9,
          element_id: '4.C.1.b.1.f',
          domain: null,
        },
      ],
    },
    {
      id: TOP_ITEM_ID,
      rank: 1,
      onetsoc_code: '25-1021.00',
      title: 'Computer Science Teachers, Postsecondary',
      job_zone: 5,
      distance: 0.167,
      raw_similarity: 0.833,
      recommendation_score: 0.833,
      explanation:
        'Computer Science Teachers, Postsecondary was recommended because your profile aligns on Professional Advising and related O*NET features. Match scores are similarity, not predicted success.',
      job_zone_note: 'Most of these occupations require graduate school.',
      work_activities: ['Training and Teaching Others', 'Working with Computers'],
      contributing_features: [
        {
          block: 'sia',
          element_id: '1.B.3.ad',
          element_name: 'Professional Advising',
          student_raw: 7,
          student_normalized: 1,
          occupation_raw: 4.67,
          occupation_normalized: 0.612,
          note: 'Selected area is also important in this occupation',
        },
        {
          block: 'knowledge',
          element_id: '2.C.1.a',
          element_name: 'Administration and Management',
          student_raw: 5,
          student_normalized: 1,
          occupation_raw: 4.2,
          occupation_normalized: 0.7,
          note: 'Selected area is also important in this occupation',
        },
        {
          block: 'essential_skills',
          element_id: '2.A.1.c',
          element_name: 'Writing',
          student_raw: 3,
          student_normalized: 0.5,
          occupation_raw: 4,
          occupation_normalized: 0.65,
          note: 'Student rating and occupational importance are both high',
        },
      ],
      rule_flags: [],
      penalties: [],
    },
    {
      id: MID_ITEM_ID,
      rank: 2,
      onetsoc_code: '25-1031.00',
      title: 'Architecture Teachers, Postsecondary',
      job_zone: 5,
      distance: 0.17,
      raw_similarity: 0.83,
      recommendation_score: 0.83,
      explanation:
        'Architecture Teachers, Postsecondary was among the nearest O*NET occupation profiles to your assessment. Match scores are similarity, not predicted success.',
      job_zone_note: 'Most of these occupations require graduate school.',
      work_activities: ['Training and Teaching Others'],
      contributing_features: [],
      rule_flags: [],
      penalties: [],
    },
  ],
}

export const mockOccupation: OccupationDetail = {
  onetsoc_code: '25-1021.00',
  title: 'Computer Science Teachers, Postsecondary',
  description: 'Teach courses in computer science. Includes both teachers primarily engaged in teaching and those who do a combination of teaching and research.',
  job_zone: 5,
  knn_complete: true,
  recommendable: true,
  has_education: true,
  has_work_context: true,
  feature_version: 'onet_30_3_v1',
  onet_release: '30.3',
  job_zone_name: 'Job Zone Five: Extensive Preparation Needed',
  job_zone_education:
    'Most of these occupations require graduate school. For example, they may require a master\'s degree, and some require a Ph.D., M.D., or J.D. (law degree).',
  job_zone_experience: 'Extensive skill, knowledge, and experience are needed for these occupations.',
  feature_count: 80,
  education: [
    { category: '8', description: "Master's Degree", percent: 54.99 },
    { category: '6', description: "Bachelor's Degree", percent: 23.4 },
  ],
  work_activities: [
    { element_id: '4.A.4.b.3', name: 'Training and Teaching Others', importance: 4.8 },
    { element_id: '4.A.3.b.1', name: 'Working with Computers', importance: 4.6 },
  ],
  interests: [{ element_id: '1.B.1.b', element_name: 'Investigative', value: 6.7 }],
}

export const mockRating: RatingOut = {
  id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
  item_id: TOP_ITEM_ID,
  relevance_1_to_5: 4,
  comment: 'Useful as a discussion prompt',
  created_at: '2026-08-24T00:45:00Z',
  note: 'This is user relevance feedback, not a measure of recommendation accuracy.',
}

export const dashboardWithRun: Dashboard = {
  user: studentUser,
  has_completed_assessment: true,
  latest_assessment: {
    id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
    status: 'completed',
    questionnaire_version: 'questionnaire_v1',
    feature_version: 'onet_30_3_v1',
    started_at: '2026-08-24T00:30:00Z',
    completed_at: '2026-08-24T00:39:00Z',
  },
  latest_recommendation: {
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
