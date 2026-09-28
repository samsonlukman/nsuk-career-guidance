import { FormEvent, useEffect, useState } from 'react'

import {
  createFacultyPrior,
  deleteFacultyPrior,
  fetchFacultyPriorAudits,
  fetchFacultyPriorCatalog,
  fetchFacultyPriors,
  updateFacultyPrior,
} from '../../api/admin'
import { ApiError } from '../../api/client'
import { Alert } from '../../components/Alert'
import { EmptyState } from '../../components/EmptyState'
import { FormField } from '../../components/FormField'
import { PageHeader } from '../../components/PageHeader'
import { Spinner } from '../../components/Spinner'
import type {
  FacultyKnowledgeCatalog,
  FacultyKnowledgePrior,
  FacultyKnowledgePriorAudit,
} from '../../types/admin'
import { formatDateTime } from '../../utils/formatDate'

export function AdminFacultyPriorsPage() {
  const [catalog, setCatalog] = useState<FacultyKnowledgeCatalog | null>(null)
  const [priors, setPriors] = useState<FacultyKnowledgePrior[]>([])
  const [audits, setAudits] = useState<FacultyKnowledgePriorAudit[]>([])
  const [faculty, setFaculty] = useState('')
  const [elementId, setElementId] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  async function reload() {
    const [catalogPayload, priorPayload, auditPayload] = await Promise.all([
      fetchFacultyPriorCatalog(),
      fetchFacultyPriors(),
      fetchFacultyPriorAudits({ page: 1, page_size: 20 }),
    ])
    setCatalog(catalogPayload)
    setPriors(priorPayload.items)
    setAudits(auditPayload.items)
    if (!faculty && catalogPayload.faculties[0]) setFaculty(catalogPayload.faculties[0])
    if (!elementId && catalogPayload.knowledge_elements[0]) {
      setElementId(catalogPayload.knowledge_elements[0].element_id)
    }
  }

  useEffect(() => {
    let cancelled = false
    reload()
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Faculty knowledge mappings could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // Initial load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    if (!faculty || !elementId) {
      setError('Choose an official faculty and an O*NET knowledge element.')
      return
    }
    setSaving(true)
    try {
      if (editingId == null) {
        await createFacultyPrior({ faculty, element_id: elementId })
        setNotice('Mapping added. Future recommendation runs will use the updated faculty knowledge prior.')
      } else {
        await updateFacultyPrior(editingId, { faculty, element_id: elementId })
        setNotice('Mapping updated. The change is recorded in the audit log.')
        setEditingId(null)
      }
      await reload()
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'The mapping could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(prior: FacultyKnowledgePrior) {
    if (!window.confirm(`Remove the ${prior.faculty} → ${prior.element_name ?? prior.element_id} mapping?`)) {
      return
    }
    setError(null)
    setNotice(null)
    try {
      await deleteFacultyPrior(prior.id)
      if (editingId === prior.id) setEditingId(null)
      setNotice('Mapping removed. The deletion is recorded in the audit log.')
      await reload()
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'The mapping could not be removed.')
    }
  }

  if (loading) return <Spinner label="Loading faculty knowledge mappings" />

  return (
    <article className="admin-page">
      <PageHeader
        eyebrow="Project configuration"
        title="Faculty → knowledge priors"
        description="These mappings are project configuration, not O*NET data. Faculty names are official NSUK faculties. Knowledge IDs come from the active O*NET snapshot."
      />
      {catalog ? <Alert tone="info">{catalog.note}</Alert> : null}
      {error ? <Alert>{error}</Alert> : null}
      {notice ? <Alert tone="info">{notice}</Alert> : null}

      <form className="form admin-prior-form" onSubmit={(event) => void handleSubmit(event)}>
        <FormField id="prior-faculty" label="Faculty">
          <select id="prior-faculty" value={faculty} onChange={(event) => setFaculty(event.target.value)}>
            {(catalog?.faculties ?? []).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField id="prior-knowledge" label="O*NET knowledge element">
          <select id="prior-knowledge" value={elementId} onChange={(event) => setElementId(event.target.value)}>
            {(catalog?.knowledge_elements ?? []).map((item) => (
              <option key={item.element_id} value={item.element_id}>
                {item.element_name} ({item.element_id})
              </option>
            ))}
          </select>
        </FormField>
        <div className="hero-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {editingId == null ? 'Add mapping' : 'Save mapping'}
          </button>
          {editingId != null ? (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setEditingId(null)}
            >
              Cancel edit
            </button>
          ) : null}
        </div>
      </form>

      <section aria-labelledby="prior-list-heading">
        <h2 id="prior-list-heading">Current mappings</h2>
        {priors.length === 0 ? (
          <EmptyState title="No faculty knowledge mappings">
            <p>The table starts empty. Add a mapping using official faculties and O*NET knowledge IDs.</p>
          </EmptyState>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th scope="col">Faculty</th>
                <th scope="col">Knowledge element</th>
                <th scope="col">Updated</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {priors.map((prior) => (
                <tr key={prior.id}>
                  <td>{prior.faculty}</td>
                  <td>
                    {prior.element_name ?? prior.element_id}
                    <div className="admin-subtle">{prior.element_id}</div>
                  </td>
                  <td>{formatDateTime(prior.updated_at)}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setEditingId(prior.id)
                        setFaculty(prior.faculty)
                        setElementId(prior.element_id)
                      }}
                    >
                      Edit
                    </button>{' '}
                    <button type="button" className="btn btn-ghost" onClick={() => void handleDelete(prior)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section aria-labelledby="prior-audit-heading">
        <h2 id="prior-audit-heading">Change history</h2>
        {audits.length === 0 ? (
          <p>No administrative changes have been recorded yet.</p>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Who</th>
                <th scope="col">Action</th>
                <th scope="col">What changed</th>
              </tr>
            </thead>
            <tbody>
              {audits.map((row) => (
                <tr key={row.id}>
                  <td>{formatDateTime(row.created_at)}</td>
                  <td>{row.actor_email ?? '—'}</td>
                  <td>{row.action}</td>
                  <td>
                    {row.faculty} → {row.element_name ?? row.element_id}
                    {row.action === 'update' && row.previous_faculty ? (
                      <div className="admin-subtle">
                        Previously {row.previous_faculty} → {row.previous_element_name ?? row.previous_element_id}
                      </div>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </article>
  )
}
