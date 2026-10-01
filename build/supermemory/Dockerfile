# Supermemory self-hosted server — multi-arch image.
#
# Upstream ships NO Docker image, so we wrap the release binary.
#
# Why debian and NOT alpine: the linux-x64 binary is dynamically linked against
# glibc (verified with readelf: NEEDED libc.so.6, highest symbol GLIBC_2.25).
# Alpine is musl-only and would fail at link time.
FROM debian:bookworm-slim

ARG SUPERMEMORY_VERSION=0.0.8

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/supermemory

# Download + verify the release's own sha256 before installing.
RUN set -eux; \
    case "$(dpkg --print-architecture)" in \
      amd64) asset=supermemory-server-linux-x64 ;; \
      arm64) asset=supermemory-server-linux-arm64 ;; \
      *) echo "unsupported arch" >&2; exit 1 ;; \
    esac; \
    base="https://github.com/supermemoryai/supermemory/releases/download/server-v${SUPERMEMORY_VERSION}"; \
    curl -fsSL -o /tmp/sm "${base}/${asset}"; \
    curl -fsSL -o /tmp/sm.sha256 "${base}/${asset}.sha256"; \
    cd /tmp; \
    sed "s#  .*#  sm#" sm.sha256 | sha256sum -c -; \
    install -m 0755 /tmp/sm /usr/local/bin/supermemory-server; \
    rm -f /tmp/sm /tmp/sm.sha256

# Non-root; uid 1000 matches umbrelOS so the bind-mounted data dir stays
# owned by the host user rather than becoming root-owned.
RUN useradd --system --uid 1000 --create-home --shell /usr/sbin/nologin supermemory \
 && mkdir -p /var/lib/supermemory \
 && chown -R supermemory:supermemory /var/lib/supermemory /opt/supermemory
USER supermemory

ENV PORT=6767 \
    SUPERMEMORY_DATA_DIR=/var/lib/supermemory \
    SUPERMEMORY_EMBEDDING_RAM_LIMIT=2gb \
    SUPERMEMORY_INGEST_CONCURRENCY=2

EXPOSE 6767
VOLUME ["/var/lib/supermemory"]

# Generous start period: first boot creates the graph engine and prewarms the
# local embedding model, which can take longer than the default 30s window.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/health" || exit 1

ENTRYPOINT ["/usr/local/bin/supermemory-server"]