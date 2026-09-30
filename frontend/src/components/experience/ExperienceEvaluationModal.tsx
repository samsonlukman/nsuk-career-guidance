import { useEffect } from 'react'

import { Button } from '../Button'
import { ExperienceEvaluationForm } from './ExperienceEvaluationForm'

type ExperienceEvaluationModalProps = {
  runId: string
  open: boolean
  onClose: () => void
}

export function ExperienceEvaluationModal({ runId, open, onClose }: ExperienceEvaluationModalProps) {
  useEffect(() => {
    if (!open) return
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = previous
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-panel experience-evaluation-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="experience-eval-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <p className="eyebrow">Your experience</p>
            <h2 id="experience-eval-title">Evaluate Your Experience</h2>
          </div>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
        <p className="lede">
          Please tell us how easy the system was to use, how useful it felt, and whether the
          recommendations seemed relevant to you. This is not an accuracy test, and it does not
          change your career recommendations.
        </p>
        <ExperienceEvaluationForm runId={runId} />
      </div>
    </div>
  )
}
