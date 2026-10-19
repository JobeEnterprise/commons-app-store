# Hermes Agent — Dockage Setup

This directory contains a Docker Compose file for running Hermes Agent
via Dockage (or any Docker Compose-compatible manager).

## Differences from the Umbrel app store version

- No `app_proxy` service (direct port access, no Umbrel proxy)
- No `PROXY_AUTH_ADD` or Umbrel-specific environment variables
- Volume path is `./data` instead of `${APP_DATA_DIR}/data/hermes`
- Port 18789 is exposed directly (not behind Umbrel's authenticated proxy)

## Usage

1. Copy `.env.example` to `.env` and set a strong password
2. Run `docker compose up -d`
3. Access the dashboard at `http://<host-ip>:18789`
4. Login with the username and password from `.env`

## Data Migration

To migrate from an existing Hermes instance (e.g., the official Umbrel app):

```bash
cp -a /path/to/existing/hermes/data/. ./data/
```

This preserves memories, skills, auth tokens, sessions, and configuration.

## GPU and Memory

The Dockerfile includes:
- Vulkan/Mesa drivers for Intel integrated graphics
- Memory patch: cgroup-aware RAM sizing (respects `mem_limit` above)
- UID/GID 1000 mapping (matches Umbrel's `hermes` user)
