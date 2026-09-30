const storagePrefix = 'nsuk.experienceEval.seen.'
const memory = new Map<string, string>()

function storageKey(runId: string): string {
  return `${storagePrefix}${runId}`
}

export function hasSeenExperienceEvaluation(runId: string): boolean {
  const key = storageKey(runId)
  if (memory.get(key) === '1') return true
  try {
    if (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function') {
      return localStorage.getItem(key) === '1'
    }
  } catch {
    return false
  }
  return false
}

export function markExperienceEvaluationSeen(runId: string): void {
  const key = storageKey(runId)
  memory.set(key, '1')
  try {
    if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
      localStorage.setItem(key, '1')
    }
  } catch {
    // In-memory copy is enough for this session.
  }
}

export function resetExperienceEvaluationPrompts(): void {
  memory.clear()
}
