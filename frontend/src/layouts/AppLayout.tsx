import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/Button'
import { displayName } from '../utils/displayName'
import { SiteFooter } from './SiteFooter'

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    navigate('/', { replace: true })
    await logout()
  }

  return (
    <div className="site">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="site-header-inner">
          <NavLink className="brand" to={user?.role === 'admin' ? '/admin' : '/dashboard'}>
            <span className="brand-mark" aria-hidden="true">
              NSUK
            </span>
            <span className="brand-text">
              Career Guidance
              <small>{user ? displayName(user) : 'Signed in'}</small>
            </span>
          </NavLink>
          <nav className="site-nav" aria-label="Account">
            {user?.role === 'student' ? (
              <>
                <NavLink to="/dashboard">Dashboard</NavLink>
                <NavLink to="/assessment">Assessment</NavLink>
                <NavLink to="/profile">Profile</NavLink>
              </>
            ) : (
              <>
                <NavLink to="/admin" end>
                  Admin
                </NavLink>
                <NavLink to="/admin/students">Students</NavLink>
                <NavLink to="/admin/recommendations">Recommendations</NavLink>
                <NavLink to="/admin/faculty-priors">Faculty priors</NavLink>
              </>
            )}
            <NavLink to="/about">About</NavLink>
            <Button variant="ghost" onClick={() => void handleLogout()}>
              Log out
            </Button>
          </nav>
        </div>
      </header>
      <main id="main" className="site-main">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  )
}
