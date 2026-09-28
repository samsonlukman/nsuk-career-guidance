import type { ReactNode } from 'react'

type EmptyStateProps = {
  title: string
  children: ReactNode
}

export function EmptyState({ title, children }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <div>{children}</div>
    </div>
  )
}
