#!/usr/bin/env python3
"""Verify the commons-hermes-agent package against the Umbrel community-store contract.

Usage: python3 check.py /path/to/commons-app-store

Mutate each assertion below and confirm the script fails — a check that has only
ever passed proves nothing.
"""
import os
import sys
import yaml
from pathlib import Path


REQUIRED_MANIFEST_FIELDS = frozenset({
    "manifestVersion", "id", "category", "name", "version", "tagline",
    "description", "developer", "website", "dependencies", "repo", "support",
    "port", "gallery", "path", "submitter", "submission",
})

VALID_CATEGORIES = frozenset({
    "ai", "automation", "bitcoin", "crypto", "developer", "files",
    "finance", "media", "networking", "social",
})

STORE_ID = "commons"
APP_ID = "commons-hermes-agent"

# Upstream Hermes image (direct, not getumbrel wrapper).
UPSTREAM_IMAGE = "ghcr.io/nousresearch/hermes-agent"


def main(root: Path) -> int:
    app_dir = root / APP_ID
    if not app_dir.is_dir():
        print(f"FAIL: {app_dir} not found"); return 1

    # --- umbrel-app-store.yml exists and declares the right store ---
    store_yml = root / "umbrel-app-store.yml"
    if not store_yml.is_file():
        print("FAIL: umbrel-app-store.yml missing"); return 1
    store = yaml.safe_load(store_yml.read_text())
    if store.get("id") != STORE_ID:
        print(f"FAIL: store id is {store.get('id')!r}, expected {STORE_ID!r}")
        return 1

    # --- umbrel-app.yml ---
    manifest_path = app_dir / "umbrel-app.yml"
    if not manifest_path.is_file():
        print("FAIL: umbrel-app.yml missing"); return 1
    manifest = yaml.safe_load(manifest_path.read_text())

    missing = REQUIRED_MANIFEST_FIELDS - manifest.keys()
    if missing:
        print(f"FAIL: missing manifest fields: {sorted(missing)}"); return 1

    if manifest["id"] != APP_ID:
        print(f"FAIL: manifest id {manifest['id']!r} != folder name {APP_ID!r}"); return 1

    # store-prefix rule (community-store only)
    if not APP_ID.startswith(STORE_ID + "-"):
        print(f"FAIL: app id {APP_ID!r} does not start with {STORE_ID!r}-"); return 1

    if manifest["category"] not in VALID_CATEGORIES:
        print(f"FAIL: category {manifest['category']!r} not in {sorted(VALID_CATEGORIES)}"); return 1

    # canonical field order ( UmbrelOS diffs manifests against it )
    order = list(manifest.keys())
    expected_start = ["manifestVersion", "id", "category", "name", "version", "tagline"]
    if order[:6] != expected_start:
        print(f"FAIL: manifest field order starts {order[:6]!r}, expected {expected_start!r}")
        return 1

    if manifest.get("deterministicPassword") and manifest.get("defaultPassword") != "":
        print("FAIL: deterministicPassword true but defaultPassword not empty"); return 1

    # --- docker-compose.yml ---
    compose_path = app_dir / "docker-compose.yml"
    if not compose_path.is_file():
        print("FAIL: docker-compose.yml missing"); return 1
    compose = yaml.safe_load(compose_path.read_text())
    services = compose.get("services", {})

    if "app_proxy" not in services:
        print("FAIL: no app_proxy service"); return 1
    if "server" not in services and "web" not in services:
        print("FAIL: no server/web service"); return 1

    svc_name = "web" if "web" in services else "server"
    svc = services[svc_name]
    app_host = services["app_proxy"]["environment"].get("APP_HOST", "")
    expected_host = f"{APP_ID}_{svc_name}_1"
    if app_host != expected_host:
        print(f"FAIL: APP_HOST {app_host!r} != expected {expected_host!r}"); return 1

    app_port = services["app_proxy"]["environment"].get("APP_PORT")
    if not app_port:
        print("FAIL: APP_PORT not set on app_proxy"); return 1

    # image must be the upstream Hermes image (direct, not getumbrel wrapper)
    image = svc.get("image", "")
    if not image:
        print("FAIL: no image on server/web service"); return 1
    if not image.startswith(UPSTREAM_IMAGE + ":"):
        print(f"FAIL: image {image!r} is not the upstream Hermes image ({UPSTREAM_IMAGE}:...)")
        return 1

    # --- environment must not reference getumbrel-wrapper-only vars ---
    env = svc.get("environment", {})
    if isinstance(env, list):
        env = {e.split("=", 1)[0]: e.split("=", 1)[1] for e in env if "=" in e}
    for forbidden in ("HERMES_UMBREL_APP_PROXY_AUTH", "HERMES_UPSTREAM_TUI_ENTRY"):
        if forbidden in env:
            print(f"FAIL: {forbidden} is a getumbrel-wrapper-only var, not supported by upstream image")
            return 1

    # --- dashboard basic auth must use $APP_PASSWORD when deterministicPassword is set ---
    if manifest.get("deterministicPassword"):
        dashboard_pw = env.get("HERMES_DASHBOARD_BASIC_AUTH_PASSWORD", "")
        if "${APP_PASSWORD}" not in dashboard_pw:
            print("FAIL: deterministicPassword set but HERMES_DASHBOARD_BASIC_AUTH_PASSWORD is not $APP_PASSWORD")
            return 1
        if "HERMES_DASHBOARD_BASIC_AUTH_USERNAME" not in env:
            print("FAIL: deterministicPassword set but HERMES_DASHBOARD_BASIC_AUTH_USERNAME missing")
            return 1
    volumes = svc.get("volumes", [])
    for v in volumes:
        if isinstance(v, str) and "${APP_DATA_DIR}/data/" not in v:
            print(f"FAIL: volume {v!r} does not use ${APP_DATA_DIR}/data/ prefix"); return 1

    # --- every bind-mount source dir has a .gitkeep ---
    for v in volumes:
        if isinstance(v, str) and "${APP_DATA_DIR}/data/" in v:
            # extract the source subpath, e.g. ${APP_DATA_DIR}/data/hermes -> data/hermes
            src = v.split(":")[0]
            rel = src.replace("${APP_DATA_DIR}/", "")
            gitkeep = app_dir / rel / ".gitkeep"
            if not gitkeep.is_file():
                print(f"FAIL: {gitkeep} missing (volume source dir {rel} has no .gitkeep)"); return 1

    # --- hooks/pre-start exists and is executable ---
    pre_start = app_dir / "hooks" / "pre-start"
    if not pre_start.is_file():
        print("FAIL: hooks/pre-start missing"); return 1
    if not os.access(pre_start, os.X_OK):
        print("FAIL: hooks/pre-start not executable"); return 1

    # --- no hardcoded password in compose ---
    compose_text = compose_path.read_text()
    if "change-me" in compose_text or "password123" in compose_text:
        print("FAIL: hardcoded password found in docker-compose.yml"); return 1

    # --- port not reserved ---
    port = manifest.get("port")
    if port in (80, 443, 2000):
        print(f"FAIL: port {port} conflicts with reserved host ports"); return 1

    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/ayham/projects/commons-app-store")
    sys.exit(main(root))
