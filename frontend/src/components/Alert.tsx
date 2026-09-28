import type { ReactNode } from 'react'

type AlertProps = {
  tone?: 'error' | 'info'
  children: ReactNode
}

export function Alert({ tone = 'error', children }: AlertProps) {
  return (
    <div className={`alert alert-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}
