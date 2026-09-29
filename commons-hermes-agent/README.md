# commons-hermes-agent

Hermes Agent in the Commons community app store.

Copied from the official `getumbrel/umbrel-apps/hermes-agent` formula, updated to
v2026.9.24 (upstream v0.21.5).

## Structure

```
commons-hermes-agent/
├── umbrel-app.yml       # manifest (id: commons-hermes-agent)
├── docker-compose.yml   # app_proxy + web services
├── hooks/
│   └── pre-start        # data dir ownership migration
├── data/
│   └── hermes/
│       └── .gitkeep     # bind-mount source dir
└── check.py             # contract assertions (run before push)
```

## Image

`ghcr.io/getumbrel/hermes-agent-umbrel:v2026.9.24` — getumbrel's Umbrel-wrapped
Hermes image. **This tag does not exist yet on GHCR** (getumbrel's last update was
2026-09-17 for v2026.9.14). Before installing, either:

- wait for getumbrel to publish `v2026.9.24`, or
- build your own wrapper from `nousresearch/hermes-agent:v2026.9.24` following the
  upstream Dockerfile's s6/dashboard/TUI wiring, or
- fall back to `v2026.9.14` (the version currently in the official store).

Once the tag exists, pin it with the multi-arch index digest:

```sh
docker buildx imagetools inspect ghcr.io/getumbrel/hermes-agent-umbrel:v2026.9.24
```

and paste the `linux/amd64,linux/arm64` index digest into `docker-compose.yml` as
`image: ghcr.io/getumbrel/hermes-agent-umbrel:v2026.9.24@sha256:<digest>`.

## Gallery images

The official store's `1.jpg`–`4.jpg` are not in the public repo tree (404 on
raw.githubusercontent.com). Replace the `gallery:` entries in `umbrel-app.yml`
with either local files committed here, or remote URLs that UmbrelOS can reach.

## Verify before push

```sh
cd /home/ayham/projects/commons-app-store
python3 commons-hermes-agent/check.py .
```

Then run the official linter against the store:

```sh
gh api -q .content repos/getumbrel/umbrel-apps/contents/.tools/lint-apps.mjs \
  | base64 -d > .tools/lint-apps.mjs
gh api -q .content repos/getumbrel/umbrel-apps/contents/package.json \
  | base64 -d > package.json
npm install
node .tools/lint-apps.mjs commons-hermes-agent --root . --check-images
```

Confirm the linter isn't silently passing by injecting a known error (e.g.
`category: bogus` in the manifest) and re-running.

## Store prefix

This is a community store — the app id **must** be `commons-hermes-agent`, not
`hermes-agent`. A mismatch silently hides the app (store shows 0 apps). The
`check.py` enforces this.

## Upstream references

- Official formula: https://github.com/getumbrel/umbrel-apps/tree/main/hermes-agent
- Upstream releases: https://github.com/NousResearch/hermes-agent/releases
- Packaging skill: `umbrel-app-packaging` (in ~/.hermes/skills)
