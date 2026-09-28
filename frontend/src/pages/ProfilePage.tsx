import { useEffect, useState, type FormEvent } from 'react'

import { fetchProfileOptions } from '../api/metadata'
import { updateProfile } from '../api/me'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { describedByFor, FormField } from '../components/FormField'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import type { ProfileOptions } from '../types/api'

const EMPTY_OPTIONS: ProfileOptions = {
  faculties: [],
  levels: [],
  further_study: [],
  course_relatedness: [],
}

export function ProfilePage() {
  const { user, setUser } = useAuth()
  const [options, setOptions] = useState<ProfileOptions>(EMPTY_OPTIONS)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const [firstName, setFirstName] = useState(user?.profile.first_name ?? '')
  const [lastName, setLastName] = useState(user?.profile.last_name ?? '')
  const [matricNumber, setMatricNumber] = useState(user?.profile.matric_number ?? '')
  const [faculty, setFaculty] = useState(user?.profile.faculty ?? '')
  const [department, setDepartment] = useState(user?.profile.department ?? '')
  const [level, setLevel] = useState(user?.profile.level ?? '')
  const [furtherStudy, setFurtherStudy] = useState(user?.profile.further_study ?? '')
  const [courseRelatedness, setCourseRelatedness] = useState(user?.profile.course_relatedness ?? '')

  useEffect(() => {
    let cancelled = false
    fetchProfileOptions()
      .then((data) => {
        if (!cancelled) setOptions(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Unable to load profile options.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    setSaving(true)
    try {
      const updated = await updateProfile({
        first_name: firstName,
        last_name: lastName,
        matric_number: matricNumber,
        faculty: faculty || null,
        department: department,
        level: level || null,
        further_study: furtherStudy || null,
        course_relatedness: courseRelatedness || null,
      })
      setUser(updated)
      setNotice('Profile saved.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to save your profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <Spinner label="Loading profile options" />
  }

  return (
    <article className="auth-page">
      <PageHeader
        eyebrow="Student record"
        title="Profile"
        description="These fields match the academic information used by the approved questionnaire. Department is free text because this project does not ship an invented NSUK department list."
      />
      {error ? <Alert>{error}</Alert> : null}
      {notice ? <Alert tone="info">{notice}</Alert> : null}
      <form className="form" onSubmit={(event) => void handleSubmit(event)}>
        <FormField id="first_name" label="First name">
          <input id="first_name" name="first_name" value={firstName} onChange={(event) => setFirstName(event.target.value)} />
        </FormField>
        <FormField id="last_name" label="Last name">
          <input id="last_name" name="last_name" value={lastName} onChange={(event) => setLastName(event.target.value)} />
        </FormField>
        <FormField id="matric_number" label="Matriculation number">
          <input
            id="matric_number"
            name="matric_number"
            value={matricNumber}
            onChange={(event) => setMatricNumber(event.target.value)}
          />
        </FormField>
        <FormField id="faculty" label="Faculty">
          <select id="faculty" name="faculty" value={faculty} onChange={(event) => setFaculty(event.target.value)}>
            <option value="">Select a faculty</option>
            {options.faculties.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField
          id="department"
          label="Programme / department"
          hint="Type the name used by your faculty. This list is not hard-coded."
        >
          <input
            id="department"
            name="department"
            value={department}
            onChange={(event) => setDepartment(event.target.value)}
            aria-describedby={describedByFor('department', 'hint')}
          />
        </FormField>
        <FormField id="level" label="Level">
          <select id="level" name="level" value={level} onChange={(event) => setLevel(event.target.value)}>
            <option value="">Select a level</option>
            {options.levels.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </FormField>
        <FormField id="further_study" label="Interest in further study">
          <select
            id="further_study"
            name="further_study"
            value={furtherStudy}
            onChange={(event) => setFurtherStudy(event.target.value)}
          >
            <option value="">Not specified</option>
            {options.further_study.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </FormField>
        <FormField id="course_relatedness" label="Course relatedness preference">
          <select
            id="course_relatedness"
            name="course_relatedness"
            value={courseRelatedness}
            onChange={(event) => setCourseRelatedness(event.target.value)}
          >
            <option value="">Not specified</option>
            {options.course_relatedness.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </FormField>
        <p className="field-hint">
          Signed in as <strong>{user?.email}</strong>. Email changes are not available in this step.
        </p>
        <Button type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Save profile'}
        </Button>
      </form>
    </article>
  )
}
