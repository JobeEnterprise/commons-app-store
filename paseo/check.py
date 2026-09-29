#!/usr/bin/env python3
"""Validate the commons-paseo package against Umbrel packaging rules.

Run: python3 check.py
Exits 0 on pass, 1 with a list of violations otherwise.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml: pip install pyyaml")

APP_ID = "paseo"
HERE = Path(__file__).parent
manifest = yaml.safe_load((HERE / "umbrel-app.yml").read_text())
compose = yaml.safe_load((HERE / "docker-compose.yml").read_text())

errors = []

# --- manifest -------------------------------------------------------------
REQUIRED = [
    "manifestVersion", "id", "category", "name", "version", "tagline",
    "description", "developer", "website", "dependencies", "repo", "support",
    "port", "gallery", "path", "submitter", "submission",
]
for key in REQUIRED:
    if key not in manifest:
        errors.append(f"manifest: missing required field '{key}'")

if manifest.get("id") != APP_ID:
    errors.append(f"manifest: id is {manifest.get('id')!r}, must equal folder name {APP_ID!r}")
if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(manifest.get("id", ""))):
    errors.append("manifest: id must be lowercase kebab-case")
if str(manifest.get("manifestVersion")) != "1":
    errors.append("manifest: manifestVersion should be 1 unless newer framework behaviour is required")
if manifest.get("category") not in {
    "ai", "automation", "bitcoin", "crypto", "developer", "files",
    "finance", "media", "networking", "social",
}:
    errors.append(f"manifest: invalid category {manifest.get('category')!r}")
if not re.fullmatch(r"\d+\.\d+\.\d+[\w.\-+]*", str(manifest.get("version", ""))):
    errors.append("manifest: version must be an upstream release version, not 'latest' or a digest")

# deterministicPassword is only valid if the password is actually wired to
# APP_PASSWORD in compose, otherwise Umbrel displays a password the app ignores.
if manifest.get("deterministicPassword"):
    svc = (compose.get("services") or {}).get("server") or {}
    env = svc.get("environment") or {}
    if not any("APP_PASSWORD" in str(v) for v in env.values()):
        errors.append("manifest: deterministicPassword is set but compose does not wire APP_PASSWORD")

# --- compose --------------------------------------------------------------
services = compose.get("services") or {}
if "app_proxy" not in services:
    errors.append("compose: missing app_proxy service")
else:
    proxy_env = services["app_proxy"].get("environment") or {}
    host = str(proxy_env.get("APP_HOST", ""))
    if host != f"{APP_ID}_server_1":
        errors.append(f"compose: APP_HOST is {host!r}, expected {APP_ID + '_server_1'!r}")
    if not proxy_env.get("APP_PORT"):
        errors.append("compose: app_proxy is missing APP_PORT")
    if str(proxy_env.get("PROXY_AUTH_ADD", "")).lower() == "true":
        errors.append("compose: PROXY_AUTH_ADD 'true' is the framework default; omit it")

if "server" not in services:
    errors.append("compose: missing server service")
else:
    server = services["server"]
    image = str(server.get("image", ""))

    # Tag and digest must travel together and describe the same tag.
    if image.endswith(":latest") or ":latest@" in image:
        errors.append("compose: image uses 'latest'; pin a version tag")
    if "@sha256:" not in image:
        errors.append("compose: image is not digest-pinned")
    else:
        tagged, _, digest = image.partition("@")
        if ":" not in tagged.rsplit("/", 1)[-1]:
            errors.append("compose: digest-pinned image must keep its version tag alongside the digest")
        elif not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            errors.append("compose: digest is not a valid sha256")

    # Forcing a user breaks first-run volume setup for root-then-drop entrypoints.
    if "user" in server:
        errors.append("compose: explicit 'user' breaks first-run volume setup on root-then-drop images")

    if server.get("restart") not in ("on-failure", "unless-stopped"):
        errors.append(f"compose: restart is {server.get('restart')!r}, expected on-failure or unless-stopped")

    env = server.get("environment") or {}
    # Paseo rejects unknown Host headers, and only trusts loopback proxies.
    # PASEO_TRUSTED_PROXIES is deliberately NOT set: it needs NETWORK_IP in a
    # CIDR-parseable form and the daemon hard-crashes on a bare address, and on
    # Umbrel's plain-HTTP LAN it buys nothing.
    for needed, why in [
        ("PASEO_HOSTNAMES", "otherwise the UI 403s behind Umbrel's proxy"),
    ]:
        if needed not in env:
            errors.append(f"compose: {needed} must be set — {why}")

    volumes = [str(v) for v in (server.get("volumes") or [])]
    if not volumes:
        errors.append("compose: server persists nothing; containers are recreated on update")
    for vol in volumes:
        if vol.startswith("/") or not vol.startswith("${APP_DATA_DIR}/data/"):
            errors.append(f"compose: volume {vol!r} must live under ${{APP_DATA_DIR}}/data/")

# Every bind-mount source dir must exist in git, or Docker creates it root-owned.
for vol in [str(v) for v in (services.get("server", {}).get("volumes") or [])]:
    src = vol.split(":")[0]
    if not src.startswith("${APP_DATA_DIR}/"):
        continue
    rel = src.removeprefix("${APP_DATA_DIR}/")
    if not (HERE / rel).is_dir():
        errors.append(f"compose: bind-mount source data/{rel} is not committed; add data/{rel}/.gitkeep")

# --- report ---------------------------------------------------------------
if errors:
    print(f"FAIL ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK  {manifest['id']} v{manifest['version']}  port {manifest['port']}  "
      f"image {services['server']['image']}")
