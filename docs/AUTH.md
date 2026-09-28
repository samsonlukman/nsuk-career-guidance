# Authentication

The React website authenticates against FastAPI with a **server-signed JWT stored in an httpOnly cookie**. This replaces the Step 10 development header `X-Actor-Id`.

## Why this approach

The product is a first-party web application (Vite dev server proxies `/api` to FastAPI; production can serve both on one host).

| Requirement | How it is met |
|---|---|
| No plaintext passwords | Argon2id hashes in `users.password_hash` |
| No secrets in React | `AUTH_SECRET` stays on the server |
| Token not readable by JavaScript | `HttpOnly` cookie `nsuk_session` |
| CSRF reduced for typical browser navigation | `SameSite=Lax` plus Origin allow-list on cookie-authenticated mutations |
| HTTPS in production | set `AUTH_COOKIE_SECURE=true` |
| Role handling | Authorization uses the database `users.role`, not a client-supplied role |

Access tokens are **not** stored in `localStorage` or returned in JSON for the frontend to persist.

## Cookie and token

- Cookie name: `nsuk_session`
- Algorithm: HS256
- Claims: `sub` (user id), `role`, `iat`, `exp`
- Lifetime: `AUTH_TOKEN_MINUTES` (default 720)

The frontend sends cookies with `credentials: "include"`. It never reads or writes the session cookie.

## Endpoints

| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/auth/register` | public; sets cookie; always creates a **student** |
| POST | `/api/v1/auth/login` | public; sets cookie |
| POST | `/api/v1/auth/logout` | clears cookie |
| GET | `/api/v1/auth/me` | session required |
| GET | `/api/v1/me/dashboard` | student session |
| PUT | `/api/v1/me/profile` | student session |

Public registration cannot create an admin account.

## Authorization

Student-scoped routes use the session user, not a client-supplied student id. `GET /api/v1/students/{student_id}/recommendations` succeeds only when the session user is that student or an admin.

## Local configuration

```
AUTH_SECRET=replace-with-a-long-random-string
AUTH_COOKIE_SECURE=false
AUTH_TOKEN_MINUTES=720
```

Do not commit a real `AUTH_SECRET`.

## CSRF (cookie sessions)

SameSite=Lax stops a typical cross-site form POST from sending `nsuk_session`. That is not comprehensive CSRF protection by itself.

Authenticated mutations also reject a present `Origin` that is not in `CORS_ORIGINS`. Same-origin clients and the automated test client may omit `Origin`. This is defense in depth, not a claim of complete CSRF coverage. Residual risks include same-site attackers, XSS, and a later change to `SameSite=None`.

Production cookie settings:

```
AUTH_COOKIE_SECURE=true
AUTH_SECRET=<long random value, environment only>
```

The Secure flag is required when the site is served over HTTPS. Leave it `false` only for local HTTP development.
