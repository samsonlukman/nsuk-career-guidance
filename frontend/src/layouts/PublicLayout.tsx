import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { SiteFooter } from './SiteFooter'

export function PublicLayout() {
  const { user } = useAuth()

  return (
    <div className="site">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="site-header-inner">
          <NavLink className="brand" to="/">
            <span className="brand-mark" aria-hidden="true">
              NSUK
            </span>
            <span className="brand-text">
              Career Guidance
              <small>Nasarawa State University, Keffi</small>
            </span>
          </NavLink>
          <nav className="site-nav" aria-label="Primary">
            <NavLink to="/" end>
              Home
            </NavLink>
            <NavLink to="/about">About</NavLink>
            {user ? (
              <NavLink to={user.role === 'admin' ? '/admin' : '/dashboard'}>
                {user.role === 'admin' ? 'Admin' : 'Dashboard'}
              </NavLink>
            ) : (
              <>
                <NavLink to="/login">Log in</NavLink>
                <NavLink to="/register">Register</NavLink>
              </>
            )}
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
