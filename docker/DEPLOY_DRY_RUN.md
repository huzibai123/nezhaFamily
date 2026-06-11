# Deployment Dry Run

This checklist is for non-destructive deployment rehearsal. It validates Compose, Caddy, health checks, worker wiring, and required production environment variables without starting a real production instance.

## Required Production Environment

Production must provide these values before `docker compose -f docker-compose.prod.yml up -d`:

- `POSTGRES_PASSWORD`: strong PostgreSQL password
- `REDIS_PASSWORD`: strong Redis password
- `SECRET_KEY`: JWT signing secret, generated with a command such as `openssl rand -hex 32`
- `ALLOWED_ORIGINS`: comma-separated browser origins, for example `https://family.example.com`
- `DOMAIN`: public hostname without `http://` or `https://`
- `ADMIN_EMAIL`: certificate notification email for Caddy/Let's Encrypt
- `TRUSTED_PROXY_COUNT=1`: one trusted proxy layer, `Caddy -> backend`

AI stays off by default:

- `AI_ENABLED=false`
- `AI_API_KEY` may be empty

## Runtime Checks

- Backend health endpoint: `GET /health`
- Backend Compose healthcheck: `curl -f http://localhost:8000/health`
- Worker command: `celery -A app.tasks.celery_app worker`
- Worker broker/result backend: Redis DB 1 and DB 2 through `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`
- Dev Caddy route: host `8080` -> Caddy `:80`; `/api/*` and `/media/*` -> backend, all other paths -> Vite frontend
- Prod Caddy route: `DOMAIN` with automatic HTTPS; `/api/*` and `/media/*` -> backend, all other paths -> frontend static service

## Acceptance Commands

Run from the repository root:

```bash
cd /Users/baiyi/myCode/nezhaFamily

docker compose run --rm backend pytest -q
npm --prefix frontend run build
docker compose config

POSTGRES_PASSWORD=change-me-postgres \
REDIS_PASSWORD=change-me-redis \
SECRET_KEY=change-me-secret-key-32-bytes-min \
ALLOWED_ORIGINS=https://family.example.com \
DOMAIN=family.example.com \
ADMIN_EMAIL=admin@example.com \
TRUSTED_PROXY_COUNT=1 \
AI_ENABLED=false \
docker compose -f docker-compose.prod.yml config

docker run --rm -v "$PWD/docker/Caddyfile.dev:/etc/caddy/Caddyfile:ro" caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile
docker run --rm \
  -e DOMAIN=family.example.com \
  -e EMAIL=admin@example.com \
  -v "$PWD/docker/Caddyfile:/etc/caddy/Caddyfile:ro" \
  caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile
```

Optional local smoke test:

```bash
docker compose up -d
curl -fsS http://localhost:8080/health || curl -fsS http://localhost:8080/
docker compose ps
```

If `8080` or `8443` is already occupied, check with `lsof -i :8080` and `lsof -i :8443`. Use a temporary local port change only for the rehearsal and do not commit it.
