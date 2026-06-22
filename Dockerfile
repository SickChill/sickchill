# syntax=docker/dockerfile:experimental
#
# Universal NAS-friendly Dockerfile for SickChill
# - Pre-builds venv in image (with all compiled extensions via Rust etc.)
# - At runtime, entrypoint copies the venv into your persistent datadir (e.g. /data/.venv)
# - Full PUID/PGID support (no more permission headaches on Synology/Unraid/etc.)
# - Same multi-arch + SOURCE= build logic for :latest and :develop tags
#
# docker run example see docker-compose.yaml:
# docker run -dit --name sickchill --restart=unless-stopped \
#   -e PUID=1026 -e PGID=100 -e TZ=Asia/Bangkok \
#   -v /docker/sickchill/data:/data \
#   -v /docker/downloads:/downloads \
#   -v /your_media/Series:/tv \
#   -p 8081:8081 \
#   sickchill/sickchill:develop

FROM --platform=$TARGETPLATFORM python:3.13-slim-bookworm AS base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONUNBUFFERED=1

ARG SOURCE
ARG PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple"
ARG HOME=${HOME:-}

# Poetry settings (only used during build when SOURCE=1)
ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH="$HOME/.venv"
ENV POETRY_CACHE_DIR="$HOME/.cache/pypoetry"
ENV POETRY_HOME="$HOME/.poetry"
ENV PATH=$POETRY_VIRTUALENVS_PATH/local/bin:$POETRY_VIRTUALENVS_PATH/bin:$PATH

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL

# Runtime deps (including gosu for privilege drop)
RUN mkdir -m 777 -p /sickchill "$POETRY_CACHE_DIR"
RUN sed -i "s/Components: main/Components: main contrib non-free/" /etc/apt/sources.list.d/debian.sources
RUN apt-get update -qq && apt-get upgrade -yqq && \
    apt-get install -yqq curl libxml2 libxslt1.1 libffi8 libssl3 libmediainfo0v5 mediainfo unrar gosu ca-certificates && \
    apt-get clean -yqq && \
    rm -rf /var/lib/apt/lists/*

FROM base AS builder
RUN apt-get update -qq && apt-get upgrade -yqq && \
    apt-get install -yqq build-essential python3-distutils-extra python3-dev \
    libxml2-dev libxslt1-dev libffi-dev libssl-dev libmediainfo-dev findutils sed && \
    apt-get clean -yqq && \
    rm -rf /var/lib/apt/lists/*

# Fixed venv path for the pre-built environment that will be copied to persistent storage
ENV VENV_IMAGE_PATH=/opt/sickchill/.venv
ENV HOME="/root/"
ENV CARGO_HOME="/root/.cargo"
ENV PATH="$CARGO_HOME/bin:$PATH"
ENV SHELL="/bin/sh"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN mkdir -m 755 -p "$HOME"

ENV RUSTUP_HOME "$HOME/.rustup"
ENV RUSTUP_PERMIT_COPY_RENAME "yes"
ENV RUSTUP_IO_THREADS 1
ENV CARGO_TERM_VERBOSE "true"
ENV CARGO "$CARGO_HOME/bin/cargo"

# hadolint ignore=SC2215
RUN --security=insecure curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sed "s#/proc/self/exe#$SHELL#g" | sh -s -- -y --profile minimal --default-toolchain nightly

ENV PATH "$RUSTUP_HOME/bin:$CARGO_HOME/bin:$PATH"

# Create our venv at the fixed image location (this one gets copied to persistent storage at runtime)
RUN python3 -m venv "$VENV_IMAGE_PATH" --upgrade --upgrade-deps
ENV PATH="$VENV_IMAGE_PATH/bin:$PATH"

RUN pip install -U wheel setuptools-rust

WORKDIR /sickchill
COPY . /sickchill/

# https://github.com/rust-lang/cargo/issues/8719#issuecomment-1253575253
# hadolint ignore=SC2215,SC1089
RUN --mount=type=tmpfs,target="$CARGO_HOME" if [ -z "$SOURCE" ]; then \
      pip install --upgrade "sickchill[speedups]"; \
    else \
      pip install --upgrade poetry && poetry run pip install -U setuptools-rust pycparser && \
      poetry build --no-interaction --no-ansi && pip install --upgrade "$(ls ./dist/sickchill-*.whl)[speedups]"; \
    fi

# Prepare wheels for the sickchill-wheels target (optional export)
RUN mkdir -m 777 /sickchill-wheels && \
    pip download sickchill --dest /sickchill-wheels && \
    rm -rf /sickchill-wheels/*none-any.whl && \
    rm -rf /sickchill-wheels/*.gz;

RUN if [ -z "$SOURCE" ]; then \
      rm -rf /sickchill-wheels/sickchill*.whl && \
      cp dist/sickchill*.whl /sickchill-wheels/; \
    fi

FROM scratch AS sickchill-wheels
COPY --from=builder /sickchill-wheels /

FROM base AS sickchill-final

# Copy the pre-built venv (will be deployed to persistent datadir/.venv by entrypoint)
COPY --from=builder "$VENV_IMAGE_PATH" "$VENV_IMAGE_PATH"

# Copy build info for entrypoint to detect image updates
COPY --from=builder /sickchill/BUILD_INFO /sickchill/BUILD_INFO

# Runtime configuration - datadir will also host the persistent .venv
ENV HOME=/data
ENV DATADIR=/data
ENV VENV_IMAGE_PATH=/opt/sickchill/.venv

WORKDIR /data

# Add our smart entrypoint that handles venv persistence + PUID/PGID
COPY docker-sc-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["sickchill", "--nolaunch", "--datadir", "/data", "--port", "8081"]

# Optional volumes (can be overridden in compose)
VOLUME /data

EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
    CMD bash -c 'if [ "$(curl -f http://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; elif [ "$(curl -fk https://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; else exit 1; fi'
