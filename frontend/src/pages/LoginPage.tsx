import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { describedByFor, FormField } from '../components/FormField'
import { PageHeader } from '../components/PageHeader'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const user = await login({ email, password })
      const destination = from ?? (user.role === 'admin' ? '/admin' : '/dashboard')
      navigate(destination, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to log in. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article className="auth-page">
      <PageHeader
        eyebrow="Student and staff access"
        title="Log in"
        description="Use the email and password you registered with. Your session is stored in a secure cookie, not in this page."
      />
      {error ? <Alert>{error}</Alert> : null}
      <form className="form" onSubmit={(event) => void handleSubmit(event)} noValidate>
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
        <FormField id="password" label="Password">
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-describedby={describedByFor('password')}
          />
        </FormField>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Log in'}
        </Button>
      </form>
      <p className="form-foot">
        New to the system? <Link to="/register">Create a student account</Link>
      </p>
    </article>
  )
}
