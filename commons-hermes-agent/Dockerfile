# Hermes Agent on Umbrel — Commons Edition
# Builds on the official upstream image and adds:
#   1. GPU drivers (Vulkan/Mesa) for Intel integrated graphics
#   2. Memory patch: cgroup-aware RAM sizing for container limits
#   3. Umbrel context (skills, plugins, TUI)

FROM nousresearch/hermes-agent:v0.22.2@sha256:36099926da316742423544e055d4734777105ffe6341873af5459b957d0c2919

USER root

# GPU acceleration for Hermes' built-in local model runtime.
# On Intel integrated graphics (UHD, Iris Xe) Hermes installs llama.cpp's
# Vulkan build, which needs the Vulkan loader and Mesa's drivers.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libvulkan1 mesa-vulkan-drivers && \
    rm -rf /var/lib/apt/lists/*

# Copy and apply the memory patch (cgroup-aware RAM sizing).
COPY patch-umbrel-local-memory.py /app/patch-umbrel-local-memory.py
RUN /opt/hermes/.venv/bin/python /app/patch-umbrel-local-memory.py && rm /app/patch-umbrel-local-memory.py

# Umbrel runs the upstream hermes user as UID/GID 1000.
RUN groupmod -o -g 1000 hermes && \
    usermod -u 1000 -g 1000 hermes

EXPOSE 18789
