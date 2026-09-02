# syntax=docker/dockerfile:experimental

# NAS-friendly SickChill image (dockering), based on develop packaging:
# - Pre-builds venv at a fixed path (/opt/sickchill/.venv)
# - Entrypoint copies it to persistent /data/.venv and refreshes on new GIT_SHA
# - Bakes Help & Info revision via sickchill/_revision.txt + SICKCHILL_* env
# - gosu + PUID/PGID for Synology / DSM style installs

# docker run -dit --name sickchill --restart=on-failure \
#   -e PUID=1026 -e PGID=100 -e TZ=America/New_York \
#   -v /docker/sickchill/data:/data -p 8081:8081 sickchill/sickchill:develop

FROM --platform=$TARGETPLATFORM python:3.13-slim-bookworm AS base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONUNBUFFERED=1

ARG SOURCE
ARG PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple"
# Neutral defaults — never invent "develop" (master/local builds omit or pass real ref)
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown

# Fixed venv path so runtime HOME=/data does not hide the image install
ENV VENV_IMAGE_PATH=/opt/sickchill/.venv
ENV HOME="/root/"
ENV CARGO_HOME="/root/.cargo"
ENV PATH="$VENV_IMAGE_PATH/bin:$CARGO_HOME/bin:$PATH"
ENV SHELL="/bin/sh"

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL

# Runtime deps (gosu for PUID/PGID drop)
RUN mkdir -m 777 -p /sickchill "$VENV_IMAGE_PATH"
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

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN mkdir -m 755 -p "$HOME"

ENV RUSTUP_HOME="$HOME/.rustup"
ENV RUSTUP_PERMIT_COPY_RENAME="yes"
ENV RUSTUP_IO_THREADS=1
ENV CARGO_TERM_VERBOSE="true"
ENV CARGO="$CARGO_HOME/bin/cargo"

# hadolint ignore=SC2215
RUN --security=insecure curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sed "s#/proc/self/exe#$SHELL#g" | sh -s -- -y --profile minimal --default-toolchain nightly

ENV PATH="$RUSTUP_HOME/bin:$CARGO_HOME/bin:$VENV_IMAGE_PATH/bin:$PATH"

RUN python3 -m venv "$VENV_IMAGE_PATH" --upgrade --upgrade-deps
RUN pip install -U wheel setuptools-rust
# Pin setuptools for pkg_resources compatibility (enzyme on Python 3.13)
RUN pip install --upgrade "setuptools>=70.0,<81.0"

WORKDIR /sickchill
COPY . /sickchill/

# Bake git revision for Help & Info. Skip placeholder "unknown".
ARG GIT_SHA
ARG GIT_BRANCH
RUN if [ -n "$GIT_SHA" ] && [ "$GIT_SHA" != "unknown" ]; then \
  if [ -n "$GIT_BRANCH" ] && [ "$GIT_BRANCH" != "unknown" ]; then \
    printf '%s %s\n' "$GIT_BRANCH" "$GIT_SHA" > sickchill/_revision.txt; \
  else \
    printf '%s\n' "$GIT_SHA" > sickchill/_revision.txt; \
  fi; \
fi

# https://github.com/rust-lang/cargo/issues/8719#issuecomment-1253575253
# hadolint ignore=SC2215,SC1089
RUN --mount=type=tmpfs,target="$CARGO_HOME" if [ -z "$SOURCE" ]; then \
  pip install --upgrade "sickchill[speedups]"; \
else \
  pip install --upgrade poetry && poetry run pip install -U setuptools-rust pycparser && \
  poetry build --no-interaction --no-ansi && pip install --upgrade "$(ls ./dist/sickchill-*.whl)[speedups]"; \
fi

# Ensure installed package has _revision.txt (wheel may omit gitignored file).
# Run python from /tmp so cwd (/sickchill) is not on sys.path.
RUN if [ -f sickchill/_revision.txt ]; then \
  REV_DST="$(cd /tmp && python -c 'import pathlib, sickchill; print(pathlib.Path(sickchill.__file__).parent)')" && \
  SRC="$(realpath sickchill/_revision.txt)" && \
  DST="$(realpath -m "$REV_DST/_revision.txt")" && \
  if [ "$SRC" != "$DST" ]; then cp sickchill/_revision.txt "$REV_DST/_revision.txt"; fi; \
fi

RUN mkdir -m 777 /sickchill-wheels && \
    pip download sickchill --dest /sickchill-wheels && \
    rm -rf /sickchill-wheels/*none-any.whl && \
    rm -rf /sickchill-wheels/*.gz

RUN if [ -n "$SOURCE" ]; then \
  rm -rf /sickchill-wheels/sickchill*.whl && \
  cp dist/sickchill-*.whl /sickchill-wheels/ || true; \
fi

FROM scratch AS sickchill-wheels
COPY --from=builder /sickchill-wheels /

FROM base AS sickchill-final

COPY --from=builder "$VENV_IMAGE_PATH" "$VENV_IMAGE_PATH"

# Runtime env + OCI label (builder-stage ENV/LABEL do not reach this image).
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown
ENV SICKCHILL_SHA=$GIT_SHA
ENV SICKCHILL_BRANCH=$GIT_BRANCH
LABEL org.opencontainers.image.revision=$GIT_SHA

# Image revision marker for entrypoint persistent-venv refresh (replaces cgroup hack).
# Written into the venv so cp -a carries it into /data/.venv on first start.
RUN if [ -n "$GIT_SHA" ] && [ "$GIT_SHA" != "unknown" ]; then \
      printf '%s\n' "$GIT_SHA" > /sickchill/.image_revision && \
      printf '%s\n' "$GIT_SHA" > "$VENV_IMAGE_PATH/.image_revision"; \
    else \
      printf 'unknown\n' > /sickchill/.image_revision && \
      printf 'unknown\n' > "$VENV_IMAGE_PATH/.image_revision"; \
    fi

# Runtime configuration — datadir is the accessible NAS mount
ENV HOME=/data
ENV DATADIR=/data
ENV PATH="$VENV_IMAGE_PATH/bin:$PATH"
WORKDIR /data

COPY docker-sc-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["sickchill", "--nolaunch", "--datadir", "/data", "--port", "8081"]

EXPOSE 8081
VOLUME /data /downloads /tv

HEALTHCHECK --interval=5m --timeout=3s \
    CMD bash -c 'if [ "$(curl -f http://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; elif [ "$(curl -fk https://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; else echo "sickchill is not responding" && exit 1; fi'
