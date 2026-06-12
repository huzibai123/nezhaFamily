## Summary

-

## Testing

- [ ] `docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q`
- [ ] `npm --prefix frontend run build`
- [ ] `npm --prefix frontend run test:e2e`
- [ ] `docker compose config`
- [ ] `git diff --check`

## Risk

-

## Checklist

- [ ] No real secrets, VPS notes, backups, media, or family screenshots are committed.
- [ ] Docs are updated when behavior, deployment, AI config, or tests change.
- [ ] AI failures do not block core family flows.
