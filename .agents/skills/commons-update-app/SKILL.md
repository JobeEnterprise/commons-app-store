# Commons Update App

Update an existing app package in the Commons App Store.

## When to Use

- Bumping an app to a new upstream version
- Fixing configuration issues in an existing package
- Adding/updating widgets, environment variables, or settings
- Don't use for: adding new apps (use `commons-package-app`), testing (use `commons-test-app`)

## Prerequisites

- App folder already exists in the repo
- Upstream has a new version/image available
- Know the new image tag and digest

## Procedure

1. **Pull latest**: `git pull origin master`
2. **Check upstream** for new releases, changed env vars, new config options
3. **Update `docker-compose.yml`**:
   - Bump image tag
   - Update digest: `docker buildx imagetools inspect <image>:<tag>`
   - Add/update environment variables
   - Update volumes if data layout changed
4. **Update `umbrel-app.yml`**:
   - Bump `version`
   - Update `releaseNotes` with changelog
   - Update `port` if changed
   - Update `environment` block if new settings added
5. **Update `check.py`** if structural changes were made
6. **Run validation**: `python3 commons-<app-id>/check.py .`
7. **Test on device** if possible
8. **Commit and push**

## Verification

- `python3 commons-<app-id>/check.py .` exits 0
- New image digest resolves: `docker buildx imagetools inspect <image>:<tag>`
- Release notes added to `umbrel-app.yml`
- No secrets in committed files
