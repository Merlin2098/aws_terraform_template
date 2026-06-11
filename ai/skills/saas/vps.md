# SaaS VPS Deployment

## When to use this skill

When deploying a SaaS application (FastAPI backend + React frontend) to a
self-managed VPS using Docker, Nginx, and Let's Encrypt — as an alternative to
the Railway/Vercel flow in `ai/skills/saas/deployment.md`. Use this skill when
the project requires self-hosting (cost, data residency, or infra control).

---

## Stack

| Concern | Technology |
|---|---|
| Containers | Docker + Docker Compose |
| Reverse proxy / TLS termination | Nginx |
| TLS certificates | Let's Encrypt (Certbot) |
| Process supervision | Docker Compose `restart: unless-stopped` |
| Backups | `pg_dump` + offsite copy (cron) |

---

## Compose layout

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    restart: unless-stopped
    env_file: .env.production
    expose:
      - "8000"
    depends_on:
      - db

  web:
    build: ./frontend
    restart: unless-stopped
    expose:
      - "80"

  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    expose:
      - "5432"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - api
      - web

volumes:
  pgdata:
```

If using Supabase for PostgreSQL (per `ai/skills/saas/database.md`), omit the
`db` service and point `DATABASE_URL` at the managed instance.

---

## Nginx reverse proxy + TLS

```nginx
# nginx/conf.d/app.conf
server {
    listen 80;
    server_name app.example.com api.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name app.example.com;

    ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;

    location / {
        proxy_pass http://web:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Issuing and renewing certificates

```bash
# Initial issuance (HTTP-01 challenge via the acme-challenge location above)
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d app.example.com -d api.example.com \
  --email ops@example.com --agree-tos --no-eff-email

# Renewal — run via cron twice daily; certbot is a no-op unless near expiry
docker compose run --rm certbot renew --webroot -w /var/www/certbot
docker compose exec nginx nginx -s reload
```

```cron
# /etc/cron.d/certbot-renew
0 3,15 * * * root cd /opt/app && docker compose run --rm certbot renew --webroot -w /var/www/certbot && docker compose exec nginx nginx -s reload
```

---

## Deployment workflow

```bash
# On the VPS, in the project directory
git pull origin main

docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
docker compose ps
```

For zero-downtime updates on a single-host setup, accept brief downtime during
`docker compose up -d` (containers are recreated) — this is acceptable for
small SaaS deployments. If zero-downtime is a hard requirement, that is a
distinct capability (load balancer + multiple app containers) and should be
scoped as its own task before implementing.

---

## Backups

### Database

```bash
#!/usr/bin/env bash
# scripts/backup_db.sh — run via cron daily
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/app/backups
RETENTION_DAYS=14

docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"

find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
```

```cron
# /etc/cron.d/db-backup
0 2 * * * root /opt/app/scripts/backup_db.sh >> /var/log/db_backup.log 2>&1
```

### Offsite copy

Sync the backup directory to object storage (S3, Backblaze B2, or an
equivalent) on the same schedule — a backup that lives only on the VPS it
protects does not survive a VPS-level failure.

```bash
# Append to backup_db.sh after the gzip step
aws s3 cp "${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz" \
  "s3://my-app-backups/db/db_${TIMESTAMP}.sql.gz"
```

### Restore

```bash
gunzip -c db_20260101_020000.sql.gz | docker compose exec -T db \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Test the restore procedure on a staging VPS or local Docker environment
periodically — an untested backup is not a backup.

---

## Firewall and access

- Allow only `22` (SSH, key-based auth only), `80`, and `443` inbound.
- Do not expose `5432` (Postgres) or `8000` (API) outside the Docker network —
  only Nginx listens on public ports.
- Apply OS security updates on a regular schedule (`unattended-upgrades` on
  Debian/Ubuntu).

---

## Policies (from domain)

- **No Secrets In Source Code** — `.env.production` lives only on the VPS,
  excluded via `.gitignore`, never committed.
- **Environment Specific Configuration** — separate `.env` files per
  environment; production secrets never copied to staging/dev.
- **Deploy Must Be Reproducible** — `docker compose build && docker compose up
  -d` from a clean checkout must reproduce the running stack.

---

## References

- `ai/skills/saas/deployment.md` — managed-platform alternative (Railway/Vercel)
- `ai/skills/saas/database.md` — schema, migrations run via `alembic upgrade head`
- `ai/skills/saas/domains.md` — DNS records pointing `app.`/`api.` at the VPS
- `ai/domains/saas.md` — domain overview and all policies
