import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { describedByFor, FormField } from '../components/FormField'
import { PageHeader } from '../components/PageHeader'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [matricNumber, setMatricNumber] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setSubmitting(true)
    try {
      await register({
        email,
        password,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
        matric_number: matricNumber || undefined,
      })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to create your account. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="auth-page">
      <PageHeader
        eyebrow="New student account"
        title="Register"
        description="Registration creates a student account only. You can add faculty, department, and level on your profile after you sign in."
      />
      {error ? <Alert>{error}</Alert> : null}
      <form className="form" onSubmit={(event) => void handleSubmit(event)} noValidate>
        <FormField id="first_name" label="First name">
          <input
            id="first_name"
            name="first_name"
            type="text"
            autoComplete="given-name"
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
          />
        </FormField>
        <FormField id="last_name" label="Last name">
          <input
            id="last_name"
            name="last_name"
            type="text"
            autoComplete="family-name"
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
          />
        </FormField>
        <FormField
          id="matric_number"
          label="Matriculation number"
          hint="Optional. Use the number issued by NSUK if you have it."
        >
          <input
            id="matric_number"
            name="matric_number"
            type="text"
            autoComplete="off"
            value={matricNumber}
            onChange={(event) => setMatricNumber(event.target.value)}
            aria-describedby={describedByFor('matric_number', 'Optional. Use the number issued by NSUK if you have it.')}
          />
        </FormField>
        <FormField id="email" label="Email address">
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </FormField>
        <FormField
          id="password"
          label="Password"
          hint="At least 8 characters. The server stores a hash, never the password itself."
        >
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-describedby={describedByFor(
              'password',
              'At least 8 characters. The server stores a hash, never the password itself.',
            )}
          />
        </FormField>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="form-foot">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </article>
  )
}
