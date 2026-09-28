type JobZoneNoteProps = {
  jobZone: number | null
  jobZoneName?: string | null
  jobZoneNote?: string | null
  jobZoneEducation?: string | null
  jobZoneExperience?: string | null
  headingId?: string
}

export function JobZoneNote({
  jobZone,
  jobZoneName,
  jobZoneNote,
  jobZoneEducation,
  jobZoneExperience,
  headingId = 'job-zone-heading',
}: JobZoneNoteProps) {
  return (
    <section className="job-zone-note" aria-labelledby={headingId}>
      <h3 id={headingId}>Job Zone</h3>
      <p>
        Job Zone indicates the level of education, experience, and preparation typically associated
        with this occupation.
      </p>
      {jobZone != null ? (
        <p className="status-label">
          Job Zone {jobZone}
          {jobZoneName ? ` · ${jobZoneName}` : ''}
          {jobZone === 5 ? ' · Extensive preparation is typical' : ''}
        </p>
      ) : (
        <p>No Job Zone is stored for this occupation.</p>
      )}
      {jobZoneNote ? <p>{jobZoneNote}</p> : null}
      {jobZoneEducation && jobZoneEducation !== jobZoneNote ? <p>{jobZoneEducation}</p> : null}
      {jobZoneExperience ? <p>{jobZoneExperience}</p> : null}
    </section>
  )
}
