# SaaS Deployment

## When to use this skill

When deploying a SaaS application (FastAPI backend + React frontend) to Railway or Vercel.
For AWS-specific deploys (S3, CloudFront, Lambda), see `ai/skills/frontend/react_vite_aws.md`.

---

## Platform selection

| Component | Platform | Notes |
|---|---|---|
| FastAPI backend | Railway | Supports Docker, PostgreSQL add-on, env vars |
| React frontend | Vercel | Native Vite support, preview deployments |
| PostgreSQL | Supabase | Managed; connection string injected via env var |
| Background jobs | Railway (cron) | Scheduled tasks without separate infra |

---

## Environment configuration

Each environment (development, staging, production) has its own set of environment variables.
Never share production config with development.

```
# .env.development
DATABASE_URL=postgresql://user:pass@localhost:5432/myapp_dev
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_JWT_SECRET=...
ENVIRONMENT=development

# .env.production  (never committed — set in Railway dashboard)
DATABASE_URL=...
SUPABASE_URL=...
SUPABASE_JWT_SECRET=...
ENVIRONMENT=production
```

Frontend env files:

```
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=...

# .env.production  (set in Vercel dashboard, not committed)
VITE_API_BASE_URL=https://api.myapp.com
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

---

## Backend deploy (Railway)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Railway setup

1. Create project → "Deploy from GitHub repo".
2. Set environment variables in Railway dashboard (never in source).
3. Add a PostgreSQL service if not using Supabase.
4. Configure health check: `GET /health` returning `{"status": "ok"}`.
5. Set `PORT` environment variable; Railway injects it automatically.

### Database migrations on deploy

Run Alembic migrations as a Railway release command (before the app starts):

```
Release command: alembic upgrade head
Start command:   uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Frontend deploy (Vercel)

1. Import GitHub repo in Vercel.
2. Framework preset: Vite.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Set env vars in Vercel dashboard (Production / Preview / Development separately).
6. Preview deployments are created automatically for every PR.

---

## CI/CD (GitHub Actions)

### Backend — run tests before Railway deploys

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements-dev.txt
      - run: pytest --tb=short
```

Railway auto-deploys from `main` only when the CI job passes (configure in Railway settings → "Deploy on push after CI").

### Frontend — type check and build

```yaml
# .github/workflows/frontend-ci.yml
name: Frontend CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run type-check
      - run: npm run build
```

---

## Rollback

- Railway: use the "Deployments" tab → click any prior deployment → "Redeploy".
- Vercel: use the "Deployments" tab → click any prior deployment → "Promote to Production".
- Database rollback: `alembic downgrade -1` (test this before every migration is merged).

---

## Secrets checklist

- [ ] No `.env` files committed to Git (verify `.gitignore`).
- [ ] No secrets in `Dockerfile` or GitHub Actions YAML.
- [ ] All secrets set in Railway / Vercel dashboard.
- [ ] Supabase JWT secret rotated from the default.
- [ ] Production database URL is not the same as staging.

---

## Policies (from domain)

- **No Secrets In Source Code** — all secrets via env vars set in the platform dashboard.
- **Environment Specific Configuration** — separate env sets per environment.
- **Deploy Must Be Reproducible** — any team member can reproduce the deploy from this document and the repo.

---

## References

- `ai/skills/saas/backend.md` — FastAPI app structure and health check
- `ai/skills/saas/database.md` — Alembic migration commands
- `ai/skills/saas/frontend.md` — Vite env variable usage
- `ai/skills/frontend/react_vite_aws.md` — alternative: AWS S3 + CloudFront deploy
- `ai/domains/saas.md` — domain overview and all policies
