# GitPod Dockerfile for Vibe.d Development
# Optimized for cloud-based ephemeral workspaces

FROM gitpod/workspace-full:latest

# Build arguments
ARG DMD_VERSION=2.108.1
ARG LDC_VERSION=1.36.0

USER root

# Install D language dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    zlib1g-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libevent-dev \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install DMD
WORKDIR /tmp
RUN curl -fsSL "https://downloads.dlang.org/releases/2.x/${DMD_VERSION}/dmd.${DMD_VERSION}.linux.tar.xz" -o dmd.tar.xz && \
    mkdir -p /opt/dmd && \
    tar -xf dmd.tar.xz -C /opt/dmd --strip-components=1 && \
    rm dmd.tar.xz

# Install LDC
RUN curl -fsSL "https://github.com/ldc-developers/ldc/releases/download/v${LDC_VERSION}/ldc2-${LDC_VERSION}-linux-x86_64.tar.xz" -o ldc.tar.xz && \
    mkdir -p /opt/ldc && \
    tar -xf ldc.tar.xz -C /opt/ldc --strip-components=1 && \
    rm ldc.tar.xz

# Set up PATH
ENV PATH="/opt/dmd/linux/bin64:/opt/ldc/bin:${PATH}" \
    LD_LIBRARY_PATH="/opt/dmd/linux/lib64:/opt/ldc/lib:${LD_LIBRARY_PATH}"

# Verify installations
RUN dmd --version && ldc2 --version && dub --version

# Pre-fetch Vibe.d to speed up workspace startup
USER gitpod
RUN mkdir -p /tmp/vibed-prefetch && \
    cd /tmp/vibed-prefetch && \
    echo '{"name":"prefetch","dependencies":{"vibe-d":"~>0.10.0"}}' > dub.json && \
    dub fetch vibe-d@0.10.0 || true && \
    rm -rf /tmp/vibed-prefetch

# Install useful global tools
RUN pip install --user httpie

USER root

# Install Docker Compose (for local service orchestration in GitPod)
RUN curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose

USER gitpod

WORKDIR /workspace
