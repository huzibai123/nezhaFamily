# Release Candidate Checklist

This checklist is the final gate before publishing a self-hosted Nezha Family release.
It is intentionally operational: each item should be reproducible from a clean checkout
without using real family data, VPS notes, model keys, or backups.

## 1. Required Gates

Run from the repository root:

```bash
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
npm --prefix frontend run build
E2E_BROWSER_CHANNEL=chrome npm --prefix frontend run test:e2e
docker compose config
POSTGRES_PASSWORD=change-me-postgres REDIS_PASSWORD=change-me-redis SECRET_KEY=change-me-secret-key-32-bytes-min AI_KEY_ENCRYPTION_SECRET=change-me-ai-key-secret-32-bytes-min ALLOWED_ORIGINS=https://family.example.com DOMAIN=family.example.com ADMIN_EMAIL=admin@example.com TRUSTED_PROXY_COUNT=1 AI_ENABLED=false docker compose -f docker-compose.prod.yml config
docker compose exec -T celery-worker celery -A app.tasks inspect ping --timeout=10
git diff --check
```

Validate Caddy files:

```bash
docker run --rm -v "$PWD/docker/Caddyfile.dev:/etc/caddy/Caddyfile:ro" caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker run --rm -e DOMAIN=family.example.com -e EMAIL=admin@example.com -v "$PWD/docker/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

## 2. Full E2E Write Flow

The default E2E command is safe when credentials are missing: it renders the login page and skips writes.
For the full release flow, set credentials for an existing local admin. Do not create, reset, or commit them:

```bash
E2E_BASE_URL=http://localhost:8080 \
E2E_API_URL=http://localhost:8000 \
E2E_ADMIN_USERNAME='your-local-admin' \
E2E_ADMIN_PASSWORD='your-local-password' \
E2E_BROWSER_CHANNEL=chrome \
npm --prefix frontend run test:e2e
```

Expected coverage: login, text post publish, post detail, like, comment, notifications, albums,
media library, profile edit modal, and Admin AI page. Test data uses the `E2E-NEZHA-` prefix and
is deleted by API cleanup when the test finishes. If cleanup fails, search that prefix in the
timeline and remove the test post manually.

## 3. Production Smoke Rehearsal

Use a temporary compose project and temporary host ports. Do not edit `docker-compose.prod.yml`:

```bash
cat >/tmp/nezha-prod-smoke.override.yml <<'YAML'
services:
  caddy:
    ports:
      - "18080:80"
      - "18443:443"
      - "18443:443/udp"
YAML

POSTGRES_PASSWORD=change-me-postgres \
REDIS_PASSWORD=change-me-redis \
SECRET_KEY=change-me-secret-key-32-bytes-min \
AI_KEY_ENCRYPTION_SECRET=change-me-ai-key-secret-32-bytes-min \
ALLOWED_ORIGINS=http://localhost:18080 \
DOMAIN=:80 \
ADMIN_EMAIL=admin@example.com \
TRUSTED_PROXY_COUNT=1 \
AI_ENABLED=false \
docker compose -p nezha-rc-smoke -f docker-compose.prod.yml -f /tmp/nezha-prod-smoke.override.yml up -d --build

curl -fsS http://localhost:18080/
docker exec nezha-backend curl -fsS http://localhost:8000/health
for i in 1 2 3 4 5; do
  docker exec nezha-celery-worker celery -A app.tasks.celery_app inspect ping --timeout=10 && break
  sleep 5
done

docker compose -p nezha-rc-smoke -f docker-compose.prod.yml -f /tmp/nezha-prod-smoke.override.yml down -v
rm -f /tmp/nezha-prod-smoke.override.yml
```

If local ports or existing container names make this unsafe, skip the `up` step and record the reason
in the release notes. The non-destructive config and Caddy validate gates must still pass.

## 4. Backup, Upgrade, and Rollback

- Before upgrading production, create and verify an admin backup from the UI.
- Download the verified backup to trusted storage before replacing containers.
- Upgrade with `git pull origin main`, `docker compose -f docker-compose.prod.yml build`, then `up -d`.
- If the new release fails before data changes, roll back to the previous Git commit and rebuild.
- If data migration has already run, restore only into a separate rehearsal project first; do not overwrite live volumes without a verified backup and a manual restore plan.

## 5. Current RC Notes

- Real model-provider smoke is manual only; CI and E2E use no real model keys.
- Real-domain HTTPS issuance is manual only; local validation uses Caddy config checks.
- Full restore into production data is manual only; this checklist requires backup verification and a rehearsal-first restore policy.
