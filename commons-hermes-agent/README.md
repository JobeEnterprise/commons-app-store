# commons-hermes-agent

Hermes Agent in the Commons community app store, packaged from the official
`getumbrel/umbrel-apps/hermes-agent` formula and updated to **v2026.9.24**
(upstream v0.21.5).

## Why not just copy getumbrel's template

Because it would be stale. getumbrel's official app is still on `2026.9.14`
(last updated 2026-09-17); upstream released v2026.9.24 on 2026-09-24. Copying
their template verbatim gets the old version, which defeats the point.

So this package uses the **upstream image directly** instead of getumbrel's
wrapper. Everything else — manifest shape, hooks, data layout, port, `path` —
follows their formula.

| | getumbrel wrapper | this package |
|---|---|---|
| Image | `ghcr.io/getumbrel/hermes-agent-umbrel` | `nousresearch/hermes-agent` (Docker Hub) |
| Version | 2026.9.14 (stale) | **2026.9.24** |
| Hermes code | v0.21.3 | **v0.21.5** |
| Proxy auth | `HERMES_UMBREL_APP_PROXY_AUTH: "1"` | dashboard basic auth on `$APP_PASSWORD` |
| Hermes Desktop app | blocked by app-proxy | blocked by app-proxy **and** WS-route basic-auth refusal |

## The auth substitution

The wrapper adds one thing the upstream image lacks: `HERMES_UMBREL_APP_PROXY_AUTH`,
which tells the dashboard to trust Umbrel's app-proxy instead of running its own
login. The upstream dashboard hard-requires an auth provider on non-loopback
binds (`HERMES_DASHBOARD_INSECURE` no longer disables that gate), so it needs one.

We use the bundled basic-auth provider wired to Umbrel's per-install
`$APP_PASSWORD`:

```yaml
HERMES_DASHBOARD_BASIC_AUTH_USERNAME: "admin"
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD: "${APP_PASSWORD}"
```

With `deterministicPassword: true` and `defaultPassword: ""` in the manifest,
Umbrel derives and displays the real password — so the credential it shows you is
the one the dashboard accepts. Login is **admin** + that password.

Cost: the dashboard has its own auth gate in front of the Umbrel proxy, so the
browser gets a second prompt. That part is cosmetic. The part that matters is
the **Hermes Desktop app cannot connect to this package** — see below.

## Hermes Desktop cannot connect (known limitation)

Verified on-device 2026-09-30 against umbrelOS 2.0 at 192.168.1.146.

Symptom: adding this gateway in the Hermes Desktop app fails with
`Could not connect to Hermes gateway (websocket error before open)`.

**The primary cause is Umbrel's app-proxy, not this package.** The app's
container port (18789) is never published; the manifest's `port: 18790` points at
`app_proxy`, which requires an umbrelOS session cookie before it forwards
anything:

```
18789  closed    ← the Hermes container, unreachable from the LAN
18790  OPEN      ← app_proxy, what `port:` publishes
2000   OPEN      ← umbrelOS auth

GET /api/status  → 302  Location: http://<host>:2000/app-auth?app=commons-hermes-agent&…
GET /api/ws      → 401  Unauthorized, Connection: close
```

Desktop speaks two auth protocols (`apps/desktop/electron/connection-config.ts`):
a legacy static `?token=`, or an OAuth `?ticket=` minted at
`POST /api/auth/ws-ticket` against a login cookie. Neither is an umbrelOS
credential, so the proxy 401s the upgrade. A WS upgrade cannot be redirected to a
login page, so it closes — the renderer's `error` fires before `open`
(`apps/shared/src/json-rpc-gateway.ts:282`).

The getumbrel wrapper package hits the same 401. `HERMES_UMBREL_APP_PROXY_AUTH`
removes Hermes' *own* login behind the proxy; it does not remove the proxy's.

**Secondary cause, unique to this package.** In gated mode the WS route rejects
basic auth outright — `_ws_auth_reason` in `hermes_cli/web_server_chat.py:227-231`
accepts only `?ticket=` or `?internal=`, and explicitly refuses the legacy
`?token=` so a leaked session token cannot grant access. So even with the proxy
open, Desktop would need a full password login plus ticket mint, a flow it only
runs for OAuth providers.

### Workarounds, in order of preference

1. **Use the browser dashboard** at `http://<umbrel-host>:18790/chat`. Log into
   umbrelOS once, then Hermes asks for `admin` + the displayed password. Works
   today, nothing to change.
2. **Disable app-proxy auth for this app** on the device. Hermes then answers
   directly and basic auth becomes the only wall, which Desktop's password flow
   can satisfy. This publishes Hermes to every LAN interface protected by one
   password — a real reduction in defence, so only worth it if the Desktop
   connection is required.
3. **Run the Desktop against a non-Umbrel Hermes.** A native install needs no
   proxy and no second prompt.

## Image pinning

```
nousresearch/hermes-agent:v2026.9.24@sha256:fca358f12efd65bfaaca05884166f15c0e2788375ca30d77061ac1ebc96452b7
```

The digest is the **multi-arch index** digest, covering both `linux/amd64` and
`linux/arm64` — one pin serves an x86 N5105 and a Raspberry Pi. Tag *and*
digest together; the linter requires both.

> The image is on **Docker Hub**, not ghcr.io. The upstream release notes list it
> as `nousresearch/hermes-agent:v2026.9.24` with no registry prefix, and a
> `ghcr.io/...` path returns 403 on pull. To re-verify the digest:
>
> ```sh
> docker buildx imagetools inspect nousresearch/hermes-agent:v2026.9.24
> ```

## Icon and gallery

`icon:` points at the genuine upstream app icon
(`apps/desktop/assets/icon.png`, 1024×1024) on jsDelivr, pinned to the release
tag. A remote URL rather than a committed binary: the Umbrel community-store
template uses remote URLs, and the official linter warns against committing
icon/gallery assets.

`gallery: []` is intentionally empty. The official store's `1.jpg`–`4.jpg` are
hosted privately by Umbrel and 404 when referenced by filename. Upstream ships
no web-dashboard screenshots, and the only UI images in the repo are macOS
Desktop PR assets that would misrepresent what an Umbrel user actually sees (the
web dashboard at `/chat`). **Add your own dashboard screenshots here after first
install** — only you can see what it looks like on your box.

## Verify before push

```sh
cd commons-app-store
python3 commons-hermes-agent/check.py .
```

Then the official linter:

```sh
gh api -q .content repos/getumbrel/umbrel-apps/contents/.tools/lint-apps.mjs | base64 -d > .tools/lint-apps.mjs
gh api -q .content repos/getumbrel/umbrel-apps/contents/package.json | base64 -d > package.json
npm install
node .tools/lint-apps.mjs commons-hermes-agent --root . --check-images
```

Confirm the linter isn't silently passing by injecting a known error (e.g.
`category: bogus`) and re-running.

`check.py` covers the community-store contract: store-prefix, upstream image on
Docker Hub, digest pinned, no wrapper-only env vars, `$APP_PASSWORD` wired to
dashboard basic auth, `icon` present, gallery entries as reachable URLs,
`.gitkeep` on every bind-mount source dir, executable `pre-start`.

## Store prefix

This is a community store, so the app id **must** be `commons-hermes-agent`, not
`hermes-agent`. A mismatch silently hides the app — the store just shows 0 apps,
no error, no log. `check.py` enforces it.

## Verification status

Package is well-formed; runtime reachability is only partly proven.

| Claim | State |
|---|---|
| Official linter clean | verified (and proven non-silent) |
| Digest resolves, amd64 + arm64 | verified |
| Container boots, app reaches `ready` | verified on-device |
| Browser dashboard login (`admin` + displayed password) | verified on-device |
| Hermes Desktop app connects | **does not** — app-proxy, see above |

## Upstream references

- Official formula: https://github.com/getumbrel/umbrel-apps/tree/main/hermes-agent
- Upstream repo: https://github.com/NousResearch/hermes-agent
- Releases: https://github.com/NousResearch/hermes-agent/releases
- Docker Hub: https://hub.docker.com/r/nousresearch/hermes-agent
- Packaging skill: `umbrel-app-packaging` (in `~/.hermes/skills`)
