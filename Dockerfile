# syntax=docker/dockerfile:experimental

# Universal NAS-friendly Dockerfile for SickChill
# - Pre-builds venv in image
# - Copies venv to persistent /data/.venv at runtime
# - Reliable revision detection using OCI labels for develop + release branches

FROM --platform=$TARGETPLATFORM python:3.13-slim-bookworm AS base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONUNBUFFERED=1

ARG SOURCE
ARG PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple"

# Runtime deps (including gosu)
RUN mkdir -m 777 -p /sickchill
RUN sed -i "s/Components: main/Components: main contrib non-free/" /etc/apt/sources.list.d/debian.sources
RUN apt-get update -qq && apt-get upgrade -yqq && \
    apt-get install -yqq curl libxml2 libxslt1.1 libffi8 libssl3 libmediainfo0v5 mediainfo unrar gosu ca-certificates && \
    apt-get clean -yqq && \
    rm -rf /var/lib/apt/lists/*

FROM base AS builder
RUN apt-get update -qq && apt-get upgrade -yqq && \
    apt-get install -yqq build-essential python3-dev \
    libxml2-dev libxslt1-dev libffi-dev libssl-dev libmediainfo-dev && \
    apt-get clean -yqq && \
    rm -rf /var/lib/apt/lists/*

# Fixed venv path for pre-built environment
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

RUN --security=insecure curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sed "s#/proc/self/exe#$SHELL#g" | sh -s -- -y --profile minimal --default-toolchain nightly

ENV PATH "$RUSTUP_HOME/bin:$CARGO_HOME/bin:$PATH"

RUN python3 -m venv "$VENV_IMAGE_PATH" --upgrade --upgrade-deps
ENV PATH="$VENV_IMAGE_PATH/bin:$PATH"

RUN pip install -U wheel setuptools-rust
# Pin setuptools for pkg_resources compatibility (enzyme dependency on Python 3.13)
RUN pip install --upgrade "setuptools>=70.0,<81.0"

WORKDIR /sickchill
COPY . /sickchill/

RUN --mount=type=tmpfs,target="$CARGO_HOME" if [ -z "$SOURCE" ]; then \
      pip install --upgrade "sickchill[speedups]"; \
    else \
      pip install --upgrade poetry && poetry run pip install -U setuptools-rust pycparser && \
      poetry build --no-interaction --no-ansi && pip install --upgrade "$(ls ./dist/sickchill-*.whl)[speedups]"; \
    fi

RUN pip install --upgrade "subliminal>=2.5.0,<3.0"

# Prepare wheels for sickchill-wheels target
RUN mkdir -m 777 /sickchill-wheels && \
    pip download sickchill --dest /sickchill-wheels && \
    rm -rf /sickchill-wheels/*none-any.whl /sickchill-wheels/*.gz

RUN if [ -n "$SOURCE" ]; then \
      rm -rf /sickchill-wheels/sickchill*.whl && \
      cp dist/sickchill-*.whl /sickchill-wheels/ || true; \
    fi

FROM scratch AS sickchill-wheels
COPY --from=builder /sickchill-wheels /

FROM base AS sickchill-final

COPY --from=builder "$VENV_IMAGE_PATH" "$VENV_IMAGE_PATH"

# Create reliable revision marker from build metadata (works for develop and master)
RUN REV=$(cat /proc/self/cgroup | grep -o 'docker-[0-9a-f]*' | head -1 | cut -d- -f2- || echo "unknown") && \
    echo "$REV" > /sickchill/.image_revision || echo "unknown" > /sickchill/.image_revision

# Runtime configuration
ENV HOME=/data
ENV DATADIR=/data
WORKDIR /data

COPY docker-sc-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["sickchill", "--nolaunch", "--datadir", "/data", "--port", "8081"]

EXPOSE 8081
VOLUME /data

HEALTHCHECK --interval=5m --timeout=3s \
    CMD bash -c 'if [ "$(curl -f http://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; elif [ "$(curl -fk https://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; else exit 1; fi'
