# Commons App Store Agent Guide

Use the relevant repo-local skill in `.agents/skills/`.

- Package a new app for the store: `commons-package-app`
- Update an existing app package: `commons-update-app`
- Test or verify an app package: `commons-test-app`
- Develop a new self-hosted app: `commons-develop-app`

Keep changes scoped to the requested app unless the task requires shared changes.

## Store rules

- Store ID: `commons`. Every app ID must start with `commons-`.
- App packages live in `<app-id>/` folders with `umbrel-app.yml` and `docker-compose.yml`.
- Images must be digest-pinned (tag + `@sha256:`).
- Volumes must use `${APP_DATA_DIR}/data/` prefix.
- Every app folder must have a `check.py` that exits 0 on valid, 1 on invalid.
- No secrets in git. `.env`, tokens, keys are gitignored.

## Verification

Before pushing, run all validators:

```bash
find . -name check.py -exec python3 {} . \;
```
