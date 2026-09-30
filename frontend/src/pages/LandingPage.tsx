import { ButtonLink } from '../components/Button'
import { useAuth } from '../hooks/useAuth'

export function LandingPage() {
  const { user } = useAuth()
  const startTo = user ? (user.role === 'admin' ? '/admin' : '/assessment') : '/register'

  return (
    <article className="landing">
      <section className="hero-panel">
        <p className="eyebrow">Nasarawa State University, Keffi</p>
        <h1>AI-Powered Personalized Career Guidance for NSUK Students</h1>
        <p className="lede">
          A structured assessment that compares your interests, skills, knowledge, and work
          preferences with official occupational information. The result is a shortlist of
          occupations for discussion with a counsellor — not a prediction of success.
        </p>
        <div className="hero-actions">
          <ButtonLink to={startTo}>Start Your Career Assessment</ButtonLink>
          <ButtonLink to="/about" variant="secondary">
            How the system works
          </ButtonLink>
        </div>
      </section>

      <section className="content-grid" aria-labelledby="what-heading">
        <div>
          <h2 id="what-heading">What this system is</h2>
          <p>
            This is a career exploration tool for undergraduate students of Nasarawa State
            University, Keffi. After you complete an assessment, the system suggests careers
            that match the interests, skills, and preferences you described.
          </p>
        </div>
        <div>
          <h2>Who it is for</h2>
          <p>
            It is designed for NSUK undergraduates who want structured, evidence-based prompts
            for career conversations. It is not an employment service, and it is not a substitute
            for departmental advising or the university counselling unit.
          </p>
        </div>
      </section>

      <section className="process" aria-labelledby="how-heading">
        <h2 id="how-heading">How the assessment works</h2>
        <ol className="steps">
          <li>
            <strong>Create an account</strong>
            Register with your student details so your profile and results stay with you.
          </li>
          <li>
            <strong>Complete the questionnaire</strong>
            Answer questions about academic context, Holland interests, skills, knowledge areas,
            work styles, and workplace preferences.
          </li>
          <li>
            <strong>Review a ranked shortlist</strong>
            You receive a shortlist of careers that match the profile you described.
          </li>
        </ol>
      </section>

      <section className="notice-panel" aria-labelledby="basis-heading">
        <h2 id="basis-heading">What recommendations are based on</h2>
        <p>
          Recommendations use the interests, skills, knowledge, work styles, and workplace
          preferences you provided. A higher match means a closer fit to the profile you
          described, not a forecast of employment, income, or academic performance.
        </p>
        <p>
          The system is intended to <strong>support</strong> professional career counselling. It
          does not replace counsellors, lecturers, or your own judgement.
        </p>
      </section>
    </article>
  )
}
