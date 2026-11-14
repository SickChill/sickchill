# syntax=docker/dockerfile:1

# NAS-friendly SickChill image, on the develop Python 3.14 packaging:
# - Pre-builds a template venv at /opt/sickchill/.venv (image layer; not under a volume)
# - Entrypoint copies it to /.venv/venv inside the persistent mount and launches that interpreter
# - Bakes Help & Info revision via sickchill/_revision.txt + SICKCHILL_* env
# - gosu + PUID/PGID for Synology / DSM style installs
# - Rustup uses a /proc/self/exe sed so builds do not need BuildKit security.insecure
#
# Pruned after Python 3.14: setuptools<81 (pkg_resources pin), system libmediainfo
# (pymediainfo vendors it), and python3-distutils-extra (distutils is gone).
#
# Note: Docker creates the install folder. Compose only names data and .venv inside it.
# Do not bake the runtime venv at /.venv — that path is a bind mount.
# The template stays at /opt/sickchill/.venv. The image directory /sickchill is not a volume.

# docker run -dit --name sickchill --restart=on-failure \
#   -e PUID=1026 -e PGID=100 -e TZ=America/New_York \
#   -v /docker/sickchill/data:/data \
#   -v /docker/sickchill/.venv:/.venv \
#   -p 8081:8081 sickchill/sickchill:develop

ARG PYTHON_VERSION=3.14
FROM --platform=$TARGETPLATFORM python:${PYTHON_VERSION}-slim-bookworm AS base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONUNBUFFERED=1

ARG PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple"
# Neutral defaults — never invent "develop" (master/local builds omit or pass real ref)
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown

# Template venv in the image (copied to /.venv at runtime — see entrypoint).
# Keep the template off the runtime path so the NAS mount does not erase the bake.
# Do not key the venv path off HOME: the final stage sets HOME=/data.
ENV DATADIR=/data
ENV VENV_IMAGE_PATH=/opt/sickchill/.venv
ENV VENV_RUNTIME_PATH=/.venv
ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH=/opt/sickchill/.venv
ENV POETRY_CACHE_DIR=/root/.cache/pypoetry

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL

# Runtime deps. gosu drops to PUID/PGID.
# pymediainfo vendors libmediainfo; keep unrar for rarfile and curl for HEALTHCHECK.
# The template venv is root-owned and not writable by the app. The persistent copy is the writable one.
# /sickchill and the Poetry cache stay writable for the image build.
RUN mkdir -m 777 -p /sickchill "$POETRY_CACHE_DIR" \
 && mkdir -p "$VENV_IMAGE_PATH" \
 && chmod 755 "$VENV_IMAGE_PATH"
RUN sed -i "s/Components: main/Components: main contrib non-free/" /etc/apt/sources.list.d/debian.sources
RUN apt-get update -qq && apt-get upgrade -yqq && \
    apt-get install -yqq curl libxml2 libxslt1.1 libffi8 libssl3 unrar gosu ca-certificates && \
    apt-get clean -yqq && \
    rm -rf /var/lib/apt/lists/*

FROM base AS builder

# Build tools only. Not shipped in the final image.
RUN apt-get update -qq && apt-get upgrade -yqq && \
    apt-get install -yqq build-essential python3-dev \
    libxml2-dev libxslt1-dev libffi-dev libssl-dev findutils sed && \
    apt-get clean -yqq && \
    rm -rf /var/lib/apt/lists/*

ENV HOME="/root/"
ENV CARGO_HOME="/root/.cargo"
ENV PATH="$CARGO_HOME/bin:$PATH"
ENV SHELL="/bin/sh"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN mkdir -m 755 -p "$HOME"

ENV RUSTUP_HOME="$HOME/.rustup"
ENV RUSTUP_PERMIT_COPY_RENAME="yes"
ENV RUSTUP_IO_THREADS=1
ENV CARGO_TERM_VERBOSE="true"
ENV CARGO="$CARGO_HOME/bin/cargo"

# sed replaces rustup's /proc/self/exe probe so this does not need --security=insecure.
RUN curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sed "s#/proc/self/exe#$SHELL#g" | sh -s -- -y --profile minimal --default-toolchain stable

ENV PATH="$RUSTUP_HOME/bin:$CARGO_HOME/bin:$VENV_IMAGE_PATH/bin:$PATH"

# Runtime venv (copied to the final image, then to the NAS datadir by the entrypoint).
# Poetry lives in /opt/poetry so it is not shipped.
# Do not put /opt/poetry/bin first: that venv's python/pip would hide the runtime venv.
ENV POETRY_HOME="/opt/poetry"
ENV VIRTUAL_ENV="$POETRY_VIRTUALENVS_PATH"
RUN python3 -m venv "$POETRY_VIRTUALENVS_PATH" --upgrade --upgrade-deps
RUN python3 -m venv "$POETRY_HOME" && "$POETRY_HOME/bin/pip" install -U pip poetry
RUN "$POETRY_VIRTUALENVS_PATH/bin/pip" install -U wheel setuptools-rust

WORKDIR /sickchill
# poetry.lock is gitignored, so this layer caches on pyproject.toml (plus license/readme).
COPY pyproject.toml README.md LICENSE.md COPYING.txt ./
RUN "$POETRY_HOME/bin/poetry" run pip install -U setuptools-rust pycparser

# SOURCE=1 in CI: install locked runtime deps here so rust/crypto is not rebuilt on every commit.
ARG SOURCE
# https://github.com/rust-lang/cargo/issues/8719#issuecomment-1253575253
# hadolint ignore=SC2215,SC1089
RUN --mount=type=tmpfs,target="$CARGO_HOME" \
  if [ -n "$SOURCE" ]; then \
    "$POETRY_HOME/bin/poetry" install --only main --no-root --no-interaction --no-ansi; \
  fi

COPY . /sickchill/

# Bake git revision for Help & Info. Skip placeholder "unknown" so pip-only
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown
RUN if [ -n "$GIT_SHA" ] && [ "$GIT_SHA" != "unknown" ]; then \
  if [ -n "$GIT_BRANCH" ] && [ "$GIT_BRANCH" != "unknown" ]; then \
    printf '%s %s\n' "$GIT_BRANCH" "$GIT_SHA" > sickchill/_revision.txt; \
  else \
    printf '%s\n' "$GIT_SHA" > sickchill/_revision.txt; \
  fi; \
fi

# hadolint ignore=SC2215,SC1089
RUN --mount=type=tmpfs,target="$CARGO_HOME" if [ -z "$SOURCE" ]; then \
  "$POETRY_VIRTUALENVS_PATH/bin/pip" install --upgrade sickchill; \
else \
  "$POETRY_HOME/bin/poetry" build --no-interaction --no-ansi && "$POETRY_VIRTUALENVS_PATH/bin/pip" install --upgrade "$(ls ./dist/sickchill-*.whl)"; \
fi

# Ensure installed package has _revision.txt (wheel may omit gitignored file).
# Run python from /tmp so cwd (/sickchill) is not on sys.path — otherwise
# `import sickchill` resolves to the source tree and cp is same-file.
RUN if [ -f sickchill/_revision.txt ]; then \
  REV_DST="$(cd /tmp && "$POETRY_VIRTUALENVS_PATH/bin/python" -c 'import pathlib, sickchill; print(pathlib.Path(sickchill.__file__).parent)')" && \
  SRC="$(realpath sickchill/_revision.txt)" && \
  DST="$(realpath -m "$REV_DST/_revision.txt")" && \
  if [ "$SRC" != "$DST" ]; then cp sickchill/_revision.txt "$REV_DST/_revision.txt"; fi; \
fi

RUN mkdir -m 777 /sickchill-wheels && \
 "$POETRY_VIRTUALENVS_PATH/bin/pip" download sickchill --dest /sickchill-wheels && \
 rm -rf /sickchill-wheels/*none-any.whl && \
 rm -rf /sickchill-wheels/*.gz;

# SOURCE=1 exports the wheel just built. SOURCE unset keeps the PyPI download (no dist/).
RUN if [ -n "$SOURCE" ]; then \
  rm -rf /sickchill-wheels/sickchill*.whl && \
  cp dist/sickchill-*.whl /sickchill-wheels/; \
fi

# Drop build-only tools and translation sources from the copied venv.
# Keep pip: update-manager runs `sys.executable -m pip`.
# Script file (not a shell heredoc): Dockerfile treats an unescaped `import` as an instruction.
RUN "$POETRY_VIRTUALENVS_PATH/bin/python" /sickchill/docker/strip-venv.py

FROM scratch AS sickchill-wheels
COPY --from=builder /sickchill-wheels /

FROM base AS sickchill-final

COPY --from=builder "$VENV_IMAGE_PATH" "$VENV_IMAGE_PATH"

# Runtime env + OCI label (builder-stage ENV/LABEL do not reach this image).
# Defaults are "unknown" (filtered at runtime); CI passes the real ref_name.
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown
ENV SICKCHILL_SHA=$GIT_SHA
ENV SICKCHILL_BRANCH=$GIT_BRANCH
LABEL org.opencontainers.image.revision=$GIT_SHA

# Image revision marker for entrypoint persistent-venv refresh.
# Written into the venv so cp -a carries it into /.venv on first start.
RUN if [ -n "$GIT_SHA" ] && [ "$GIT_SHA" != "unknown" ]; then \
      printf '%s\n' "$GIT_SHA" > /sickchill/.image_revision && \
      printf '%s\n' "$GIT_SHA" > "$VENV_IMAGE_PATH/.image_revision"; \
    else \
      printf 'unknown\n' > /sickchill/.image_revision && \
      printf 'unknown\n' > "$VENV_IMAGE_PATH/.image_revision"; \
    fi

# Runtime configuration - data and .venv are the mounts.
# The listen port is published by Compose, not set here.
ENV HOME=/data
ENV DATADIR=/data
ENV VENV_RUNTIME_PATH=/.venv
ENV PATH="$VENV_IMAGE_PATH/bin:$PATH"
WORKDIR /data

COPY docker-sc-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["sickchill", "--nolaunch", "--datadir", "/data"]

EXPOSE 8081
# Operator drop-in plugins: /data/plugins (host data folder, or settings.PLUGIN_DIR)
VOLUME /data /.venv /downloads /tv

HEALTHCHECK --interval=5m --timeout=3s \
    CMD bash -c 'if [ "$(curl -f http://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; elif [ "$(curl -fk https://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; else echo "sickchill is not responding" && exit 1; fi'
