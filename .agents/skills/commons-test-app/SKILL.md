# Commons Test App

Validate an app package against Commons App Store rules.

## When to Use

- Before pushing any app change
- CI validation
- Auditing existing packages
- Don't use for: adding new apps or making changes (use `commons-package-app` or `commons-update-app`)

## Prerequisites
- Python 3 with pyyaml (`pip install pyyaml`)
- Docker (for image digest verification)

## Procedure

1. **Run the app's own validator**:
   ```bash
   python3 commons-<app-id>/check.py .
   ```
2. **Run all validators**:
   ```bash
   find . -name check.py -not -path './.git/*' -exec python3 {} . \;
   ```
3. **Check for secrets**:
   ```bash
   grep -rE '(password|token|key|secret)\s*[:=]' --include='*.yml' --include='*.yaml' --include='*.env' . | grep -v '.git/' | grep -v 'APP_PASSWORD' | grep -v 'check.py' | grep -v 'README' || echo "No secrets found"
   ```
4. **Verify image digests** resolve (if Docker available):
   ```bash
   docker buildx imagetools inspect <image>:<tag>
   ```
5. **Verify no hardcoded passwords** in docker-compose files

## Verification

- All `check.py` files exit 0
- No secret patterns in committed YAML
- All image digests resolve
- Report any failures with file path and line number
