import { FormEvent, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { fetchAdminStudents } from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { Pagination } from '../../components/admin/Pagination'
import { EmptyState } from '../../components/EmptyState'
import { FormField } from '../../components/FormField'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type { AdminStudentList } from '../../types/admin'
import { formatDateTime } from '../../utils/formatDate'

export function AdminStudentsPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page') || '1')
  const query = params.get('q') || ''
  const [draft, setDraft] = useState(query)
  const [data, setData] = useState<AdminStudentList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDraft(query)
  }, [query])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchAdminStudents({ q: query || undefined, page, page_size: 20 })
      .then((payload) => {
        if (!cancelled) setData(payload)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Students could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page, query])

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const next = new URLSearchParams()
    if (draft.trim()) next.set('q', draft.trim())
    setParams(next)
  }

  if (loading && !data) return <Spinner label="Loading students" />
  if (error && !data) return <Alert>{error}</Alert>

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Student management"
        title="Students"
        description="Search and inspect stored student accounts. Passwords are never shown."
      />
      <form className="admin-filter" onSubmit={handleSearch}>
        <FormField id="student-search" label="Search students" hint="Email, name, or matriculation number.">
          <input id="student-search" value={draft} onChange={(event) => setDraft(event.target.value)} />
        </FormField>
        <button type="submit" className="btn btn-primary">
          Search
        </button>
      </form>
      {error ? <Alert>{error}</Alert> : null}
      {!data || data.items.length === 0 ? (
        <EmptyState title="No students match this search">
          <p>Registered student accounts appear here after they are created on the server.</p>
        </EmptyState>
      ) : (
        <>
          <table className="history-table">
            <caption className="visually-hidden">Registered students</caption>
            <thead>
              <tr>
                <th scope="col">Student</th>
                <th scope="col">Faculty</th>
                <th scope="col">Assessment</th>
                <th scope="col">Runs</th>
                <th scope="col">Registered</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <Link to={`/admin/students/${item.id}`}>
                      {item.first_name || item.last_name
                        ? `${item.first_name ?? ''} ${item.last_name ?? ''}`.trim()
                        : item.email}
                    </Link>
                    <div className="admin-subtle">{item.email}</div>
                    {item.matric_number ? <div className="admin-subtle">{item.matric_number}</div> : null}
                  </td>
                  <td>{item.faculty ?? '—'}</td>
                  <td>{item.latest_assessment_status ?? 'None'}</td>
                  <td>{item.recommendation_run_count}</td>
                  <td>{formatDateTime(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            page={data.page}
            totalPages={data.total_pages}
            onPageChange={(nextPage) => {
              const next = new URLSearchParams(params)
              next.set('page', String(nextPage))
              setParams(next)
            }}
          />
        </>
      )}
    </article>
  )
}
