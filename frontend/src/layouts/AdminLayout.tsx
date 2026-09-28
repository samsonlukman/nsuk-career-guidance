import { NavLink, Outlet } from 'react-router-dom'

const LINKS = [
  { to: '/admin', label: 'Overview', end: true },
  { to: '/admin/students', label: 'Students' },
  { to: '/admin/recommendations', label: 'Recommendations' },
  { to: '/admin/feedback', label: 'Feedback' },
  { to: '/admin/onet', label: 'O*NET' },
  { to: '/admin/questionnaire', label: 'Questionnaire' },
  { to: '/admin/configuration', label: 'Configuration' },
  { to: '/admin/faculty-priors', label: 'Faculty priors' },
]

export function AdminLayout() {
  return (
    <div className="admin-shell">
      <nav className="admin-nav" aria-label="Administration">
        {LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end}>
            {link.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  )
}
