export type UserRole = 'student' | 'admin'

export type StudentProfile = {
  first_name: string | null
  last_name: string | null
  matric_number: string | null
  faculty: string | null
  department: string | null
  level: string | null
  further_study: string | null
  course_relatedness: string | null
}

export type CurrentUser = {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  profile: StudentProfile
}

export type RegisterPayload = {
  email: string
  password: string
  first_name?: string
  last_name?: string
  matric_number?: string
}

export type LoginPayload = {
  email: string
  password: string
}

export type ProfileUpdatePayload = Partial<StudentProfile>
