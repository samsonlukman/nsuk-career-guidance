import { ButtonLink } from '../components/Button'
import { PageHeader } from '../components/PageHeader'

export function NotFoundPage() {
  return (
    <article className="prose-page">
      <PageHeader title="Page not found" description="That address is not part of this website." />
      <ButtonLink to="/" variant="secondary">
        Back to the home page
      </ButtonLink>
    </article>
  )
}
