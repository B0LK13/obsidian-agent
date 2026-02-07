# syntax=docker/dockerfile:1
# Advanced Vibe.d Development Environment
# Multi-stage build for optimized image size and security

FROM ubuntu:22.04 AS builder

# Build arguments for version control
ARG DMD_VERSION=2.108.1
ARG LDC_VERSION=1.36.0
ARG DUB_VERSION=1.36.0

# Environment configuration
ENV DEBIAN_FRONTEND=noninteractive \
    DMD_VERSION=${DMD_VERSION} \
    LDC_VERSION=${LDC_VERSION} \
    DUB_VERSION=${DUB_VERSION} \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    libssl-dev \
    zlib1g-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libevent-dev \
    xz-utils \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r ddev && useradd -r -g ddev -m -s /bin/bash ddev

# Install DMD (D Compiler)
WORKDIR /tmp
RUN curl -fsSL "https://downloads.dlang.org/releases/2.x/${DMD_VERSION}/dmd.${DMD_VERSION}.linux.tar.xz" -o dmd.tar.xz && \
    mkdir -p /opt/dmd && \
    tar -xf dmd.tar.xz -C /opt/dmd --strip-components=1 && \
    rm dmd.tar.xz

# Install LDC (LLVM-based D Compiler - optimized builds)
RUN curl -fsSL "https://github.com/ldc-developers/ldc/releases/download/v${LDC_VERSION}/ldc2-${LDC_VERSION}-linux-x86_64.tar.xz" -o ldc.tar.xz && \
    mkdir -p /opt/ldc && \
    tar -xf ldc.tar.xz -C /opt/ldc --strip-components=1 && \
    rm ldc.tar.xz

# Set up PATH for D compilers
ENV PATH="/opt/dmd/linux/bin64:/opt/ldc/bin:${PATH}" \
    LD_LIBRARY_PATH="/opt/dmd/linux/lib64:/opt/ldc/lib:${LD_LIBRARY_PATH}"

# Verify installations
RUN dmd --version && ldc2 --version && dub --version

# Pre-fetch common Vibe.d dependencies to cache layer
RUN mkdir -p /home/ddev/.dub && \
    chown -R ddev:ddev /home/ddev/.dub

USER ddev
WORKDIR /home/ddev

# Create a temporary project to pre-fetch vibe.d
RUN mkdir -p /tmp/vibed-prefetch && \
    cd /tmp/vibed-prefetch && \
    echo '{"name":"prefetch","dependencies":{"vibe-d":"~>0.10.0"}}' > dub.json && \
    dub fetch vibe-d@0.10.0 || true && \
    rm -rf /tmp/vibed-prefetch

USER root

# ============================================
# Runtime Stage - Minimal production image
# ============================================
FROM ubuntu:22.04 AS runtime

ARG DMD_VERSION=2.108.1
ARG LDC_VERSION=1.36.0

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 \
    zlib1g \
    libcurl4 \
    libevent-2.1-7 \
    libxml2 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r ddev && useradd -r -g ddev -m -s /bin/bash ddev

# Copy D toolchain from builder
COPY --from=builder /opt/dmd /opt/dmd
COPY --from=builder /opt/ldc /opt/ldc
COPY --from=builder /home/ddev/.dub /home/ddev/.dub

# Set ownership
RUN chown -R ddev:ddev /home/ddev/.dub

# Environment setup
ENV PATH="/opt/dmd/linux/bin64:/opt/ldc/bin:${PATH}" \
    LD_LIBRARY_PATH="/opt/dmd/linux/lib64:/opt/ldc/lib:${LD_LIBRARY_PATH}" \
    DUB_HOME="/home/ddev/.dub"

# Verify runtime installation
RUN dmd --version && ldc2 --version && dub --version

# Set up working directory
WORKDIR /app

# Default to non-root user
USER ddev

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["bash"]

# ============================================
# Development Stage - Full dev tools
# ============================================
FROM runtime AS development

USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdb \
    lldb \
    valgrind \
    strace \
    ltrace \
    linux-tools-generic \
    vim \
    nano \
    htop \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Install additional debugging support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libunwind-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

USER ddev

# Expose common ports
EXPOSE 8080 9090 5432 6379

CMD ["bash"]
