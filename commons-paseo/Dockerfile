# commons-paseo: Paseo daemon with OpenCode v2 baked in as a provider.
#
# Base image is the official Paseo release, pinned by tag + multi-arch index
# digest. We install OpenCode CLI globally so Paseo auto-discovers it as a
# provider without any post-install manual steps.
#
# OpenCode v2: https://opencode.ai/v2/install
# Paseo native provider: https://paseo.sh/docs/providers

FROM ghcr.io/getpaseo/paseo:0.11.4@sha256:0e64b56fa1f99808623f4de70321cdd292e85b6db151636c13b0e6786b0e1ba5

USER root

# Install OpenCode v2 CLI globally.
# The Paseo image already ships Node.js, so we just add the npm package.
RUN npm install -g opencode-ai@latest

# Verify installation
RUN opencode --version

USER paseo

# Paseo auto-discovers opencode on PATH. No additional config needed.
