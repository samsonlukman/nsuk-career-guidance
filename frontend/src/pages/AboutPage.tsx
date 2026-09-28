import { PageHeader } from '../components/PageHeader'

export function AboutPage() {
  return (
    <article className="prose-page">
      <PageHeader
        eyebrow="About the system"
        title="Career guidance grounded in occupational information"
        description="The NSUK Career Guidance System helps undergraduates explore occupations using a published questionnaire, official O*NET data, and a documented hybrid method."
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
        <h2>Method, in brief</h2>
        <ul>
          <li>Your answers become a student feature profile aligned to O*NET 30.3 fields.</li>
          <li>Named rules apply eligibility and flags (for example job-zone suitability).</li>
          <li>
            Remaining occupations are ranked with k-nearest neighbours using weighted-block
            cosine similarity.
          </li>
          <li>Each recommendation is explained in terms of contributing features, not fate.</li>
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

      <section>
        <h2>Data attribution</h2>
        <p>
          Occupational records come from the O*NET 30.3 Database by the U.S. Department of Labor,
          Employment and Training Administration, licensed under CC BY 4.0. Faculty names follow
          the official NSUK academic structure. Department names are entered by the student; they
          are not invented here as a fixed list.
        </p>
      </section>
    </article>
  )
}
