import { PageHeader } from '../components/PageHeader'

export function AboutPage() {
  return (
    <article className="prose-page">
      <PageHeader
        eyebrow="About the system"
        title="Career guidance for NSUK students"
        description="The NSUK Career Guidance System helps undergraduates explore careers from a structured assessment. Results are a starting point for discussion, not a decision made for you."
      />

      <section>
        <h2>Purpose</h2>
        <p>
          Students often need a structured way to connect what they enjoy and can do with the
          range of occupations that exist. This application produces a personalised shortlist
          for discussion. It does not claim guaranteed employment, guaranteed career success, or
          proven predictive accuracy.
        </p>
      </section>

      <section>
        <h2>What you do</h2>
        <ul>
          <li>Create an account and complete the career assessment.</li>
          <li>Review a shortlist of careers that match the profile you described.</li>
          <li>Read why each career was suggested, then discuss the results with a counsellor.</li>
        </ul>
      </section>

      <section>
        <h2>Professional counselling</h2>
        <p>
          Use the results as a starting point with a career counsellor or academic adviser. Human
          context — family circumstances, labour-market realities in Nigeria, and personal values
          that this questionnaire does not capture — still matters.
        </p>
      </section>
    </article>
  )
}
