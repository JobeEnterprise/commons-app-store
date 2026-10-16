# Commons Package App

Package an existing upstream application for the Commons App Store.

## When to Use

- A new upstream app needs to be added to the store
- An upstream Docker image needs to be wrapped in an Umbrel package
- Don't use for: updating existing apps (use `commons-update-app`), testing (use `commons-test-app`)

## Prerequisites

- Upstream application has a Docker image (GHCR, Docker Hub, etc.)
- Image supports linux/amd64 and linux/arm64
- `umbrel-app-store.yml` exists at repo root with `id: "commons"`

## Procedure

1. **Create folder** named `commons-<app-id>/` at repo root
2. **Write `umbrel-app.yml`** with required fields:
   - `manifestVersion: 1`
   - `id: commons-<app-id>` (must match folder name)
   - `category` from valid set: ai, automation, bitcoin, crypto, developer, files, finance, media, networking, social
   - `name`, `version`, `tagline`, `description` (with setup instructions)
   - `icon` as https URL (remote, not local binary)
   - `developer`, `website`, `repo`, `support`
   - `port` (the port app_proxy exposes)
   - `gallery` (list of https URLs)
   - `path`, `submitter`, `submission`
   - `deterministicPassword: true` if app has its own auth
3. **Write `docker-compose.yml`**:
   - `app_proxy` service with `APP_HOST`, `APP_PORT`, `PROXY_AUTH_ADD: "false"` only if app has its own auth
   - `server` or `web` service with digest-pinned image
   - Volumes under `${APP_DATA_DIR}/data/`
   - All bind-mount source dirs need `.gitkeep`
4. **Write `check.py`** — validates manifest fields, image pinning, volume paths, store prefix
5. **Add `.gitkeep`** files for every bind-mount source directory
6. **Run validation**: `python3 commons-<app-id>/check.py .`
7. **Commit and push**

## Verification

- `python3 commons-<app-id>/check.py .` exits 0
- All images have tag + `@sha256:` digest
- All volumes use `${APP_DATA_DIR}/data/` prefix
- App ID starts with `commons-`
- No secrets in committed files
