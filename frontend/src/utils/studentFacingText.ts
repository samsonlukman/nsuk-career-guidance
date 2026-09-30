/** Rewrite stored recommendation copy so students do not see data-source or method jargon. */

export function studentFacingText(text: string): string {
  let value = text
    .replace(/\brelated O\*NET features\b/gi, 'related features')
    .replace(/\bnearest O\*NET occupation profiles\b/gi, 'closest career matches')
    .replace(/\bO\*NET occupation profiles\b/gi, 'career matches')
    .replace(/\bO\*NET occupation record\b/gi, 'occupation record')
    .replace(/\bO\*NET database\b/gi, 'occupational information')
    .replace(/\bO\*NET-SOC\b/gi, '')
    .replace(/\bO\*NET(?:\s*30\.3)?\b/gi, '')
    .replace(/\bk-nearest neighbours?\b/gi, '')
    .replace(/\bKNN\b/g, '')
    .replace(/\bweighted-block cosine similarity\b/gi, 'how closely they match your answers')
    .replace(/\s{2,}/g, ' ')
    .replace(/\s+([.,;:])/g, '$1')
    .trim()

  if (/profile similarity/i.test(value) && /success|accuracy/i.test(value)) {
    return 'These scores show how closely a career matches your answers. They do not predict job success.'
  }
  return value
}

export function studentFacingNotes(notes: string[]): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const note of notes) {
    const cleaned = studentFacingText(note)
    if (!cleaned || seen.has(cleaned)) continue
    seen.add(cleaned)
    result.push(cleaned)
  }
  return result
}
