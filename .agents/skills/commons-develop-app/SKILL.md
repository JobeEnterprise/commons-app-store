# Commons Develop App

Build a new self-hosted application for the Commons App Store.

## When to Use

- Building an app from scratch (not packaging an upstream)
- Creating a custom service that runs on Umbrel
- Don't use for: packaging upstream apps (use `commons-package-app`), updating existing (use `commons-update-app`)

## Prerequisites
- Docker multi-arch build capability (buildx)
- GHCR account for publishing images
- GitHub Actions configured for CI builds

## Procedure

1. **Design the app**:
   - What does it do? What's the web UI URL?
   - What env vars does it need?
   - What data does it persist?
2. **Create folder** `commons-<app-id>/`
3. **Write `Dockerfile`** — multi-arch, pinned base image
4. **Write `docker-compose.yml`** with app_proxy + server/web service
5. **Write `umbrel-app.yml`** with full metadata
6. **Write `check.py`** — validate manifest, compose, volumes
7. **Add CI workflow** in `.github/workflows/` to build and push the image
8. **Add `.gitkeep`** for bind-mount source dirs
9. **Run validation**: `python3 commons-<app-id>/check.py .`
10. **Commit and push**

## Verification

- `python3 commons-<app-id>/check.py .` exits 0
- CI workflow builds and pushes multi-arch image
- Image digest is pinned in docker-compose.yml
- All volumes under `${APP_DATA_DIR}/data/`
- No secrets in git
