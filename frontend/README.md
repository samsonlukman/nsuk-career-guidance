# NSUK Career Guidance website

React + TypeScript student website for the NSUK career guidance system.

The FastAPI backend remains the source of truth for authentication, profiles, assessments, and recommendations. This app does not reimplement ranking or scoring.

## Development

From the repository root, run the API, then:

```bash
cd frontend
npm install
npm run dev
```

`vite` proxies `/api` to `http://127.0.0.1:8000` so the session cookie stays same-origin. See [docs/AUTH.md](../docs/AUTH.md).

```bash
npm test
```
