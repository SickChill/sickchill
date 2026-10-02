# syntax=docker/dockerfile:experimental

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v mount_point:/mount_point \
# -v /docker/sickchill/data:/data \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

FROM --platform=$TARGETPLATFORM python:3.13-slim-bookworm AS base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONUNBUFFERED=1

ARG PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple"
ARG HOME=${HOME:-}

ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH="$HOME/.venv"
ENV POETRY_CACHE_DIR="$HOME/.cache/pypoetry"
ENV POETRY_HOME="$HOME/.poetry"

ENV PATH=$POETRY_VIRTUALENVS_PATH/local/bin:$POETRY_VIRTUALENVS_PATH/bin:$PATH

# ENV SODIUM_INSTALL=system

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL

# TODO: Add a user and drop privileges, preferablty from --user argument

RUN mkdir -m 777 -p /sickchill "$POETRY_CACHE_DIR"

RUN sed -i "s/Components: main/Components: main contrib non-free/" /etc/apt/sources.list.d/debian.sources
# pymediainfo vendors libmediainfo; keep unrar for rarfile post-processing and curl for HEALTHCHECK.
RUN apt-get update -qq && apt-get upgrade -yqq && \
 apt-get install -yqq curl libxml2 libxslt1.1 libffi8 libssl3 unrar && \
 apt-get clean -yqq && \
 rm -rf /var/lib/apt/lists/*

FROM base AS builder
RUN apt-get update -qq && apt-get upgrade -yqq && \
 apt-get install -yqq build-essential python3-distutils-extra python3-dev \
 libxml2-dev libxslt1-dev libffi-dev libssl-dev libmediainfo-dev findutils sed && \
 apt-get clean -yqq && \
 rm -rf /var/lib/apt/lists/*

ENV HOME="/root/"
ENV CARGO_HOME="/root/.cargo"
ENV PATH="$CARGO_HOME/bin:$PATH"
ENV SHELL="/bin/sh"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Make sure HOME exists
RUN mkdir -m 755 -p "$HOME"

ENV RUSTUP_HOME "$HOME/.rustup"
ENV RUSTUP_PERMIT_COPY_RENAME "yes"
ENV RUSTUP_IO_THREADS 1
ENV CARGO_TERM_VERBOSE "true"
ENV CARGO "$CARGO_HOME/bin/cargo"

# hadolint ignore=SC2215
RUN --security=insecure curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sed "s#/proc/self/exe#$SHELL#g" | sh -s -- -y --profile minimal --default-toolchain stable

ENV PATH "$RUSTUP_HOME/bin:$CARGO_HOME/bin:$PATH"

# Runtime venv (copied to the final image). Poetry lives in /opt/poetry so it is not shipped.
ENV POETRY_HOME="/opt/poetry"
RUN python3 -m venv "$POETRY_VIRTUALENVS_PATH" --upgrade --upgrade-deps # upgrade-deps requires python3.9+
RUN python3 -m venv "$POETRY_HOME" && "$POETRY_HOME/bin/pip" install -U pip poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN pip install -U wheel setuptools-rust

WORKDIR /sickchill
# poetry.lock is gitignored, so this layer caches on pyproject.toml (plus license/readme).
COPY pyproject.toml README.md LICENSE.md COPYING.txt ./
RUN poetry run pip install -U setuptools-rust pycparser

# SOURCE=1 in CI: install locked runtime deps here so rust/crypto is not rebuilt on every commit.
ARG SOURCE
# https://github.com/rust-lang/cargo/issues/8719#issuecomment-1253575253
# hadolint ignore=SC2215,SC1089
RUN --mount=type=tmpfs,target="$CARGO_HOME" \
  if [ -n "$SOURCE" ]; then \
    poetry install --only main --no-root --no-interaction --no-ansi; \
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
  pip install --upgrade sickchill; \
else \
  poetry build --no-interaction --no-ansi && pip install --upgrade "$(ls ./dist/sickchill-*.whl)"; \
fi

# Ensure installed package has _revision.txt (wheel may omit gitignored file).
# Run python from /tmp so cwd (/sickchill) is not on sys.path — otherwise
# `import sickchill` resolves to the source tree and cp is same-file.
RUN if [ -f sickchill/_revision.txt ]; then \
  REV_DST="$(cd /tmp && python -c 'import pathlib, sickchill; print(pathlib.Path(sickchill.__file__).parent)')" && \
  SRC="$(realpath sickchill/_revision.txt)" && \
  DST="$(realpath -m "$REV_DST/_revision.txt")" && \
  if [ "$SRC" != "$DST" ]; then cp sickchill/_revision.txt "$REV_DST/_revision.txt"; fi; \
fi

RUN mkdir -m 777 /sickchill-wheels && \
 pip download sickchill --dest /sickchill-wheels && \
 rm -rf /sickchill-wheels/*none-any.whl && \
 rm -rf /sickchill-wheels/*.gz;

RUN if [ -z "$SOURCE" ]; then \
  rm -rf /sickchill-wheels/sickchill*.whl && \
  cp dist/sickchill*.whl /sickchill-wheels/; \
fi

# Drop build-only tools and translation sources from the copied venv.
# hadolint ignore=SC2016
RUN python - <<'PY'
import os
import shutil
import sysconfig
from pathlib import Path

root = Path(sysconfig.get_path("purelib"))
drop_names = {
    "pip",
    "wheel",
    "setuptools_rust",
    "poetry",
}
for path in list(root.iterdir()):
    name = path.name
    pkg = name.split("-", 1)[0]
    if name in drop_names or pkg in drop_names or name == "distutils-precedence.pth":
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)

for dirpath, dirnames, _filenames in os.walk(root, topdown=False):
    base = os.path.basename(dirpath)
    if base in {"__pycache__", "tests", "test", "testing"}:
        shutil.rmtree(dirpath, ignore_errors=True)

locale_dir = root / "sickchill" / "locale"
if locale_dir.is_dir():
    for extra in locale_dir.rglob("*"):
        if extra.suffix in {".po", ".pot"}:
            extra.unlink(missing_ok=True)

venv = Path(os.environ["POETRY_VIRTUALENVS_PATH"])
for binary in ("pip", "pip3", "wheel", "poetry"):
    for path in venv.joinpath("bin").glob(binary + "*"):
        path.unlink(missing_ok=True)
PY

FROM scratch AS sickchill-wheels
COPY --from=builder /sickchill-wheels /

FROM base AS sickchill-final

COPY --from=builder "$POETRY_VIRTUALENVS_PATH" "$POETRY_VIRTUALENVS_PATH"

# Runtime env + OCI label (builder-stage ENV/LABEL do not reach this image).
# Defaults are "unknown" (filtered at runtime); CI passes the real ref_name.
ARG GIT_SHA=unknown
ARG GIT_BRANCH=unknown
ENV SICKCHILL_SHA=$GIT_SHA
ENV SICKCHILL_BRANCH=$GIT_BRANCH
LABEL org.opencontainers.image.revision=$GIT_SHA

# When you docker exec, show the config files in the container
ENV HOME=/data
WORKDIR /data

# Operator drop-in plugins: /data/plugins (host: $DATA_DIR/plugins or settings.PLUGIN_DIR)
VOLUME /data /downloads /tv

CMD ["sickchill", "--nolaunch", "--datadir", "/data", "--port", "8081"]
EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
 CMD bash -c 'if [ "$(curl -f http://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; elif [ "$(curl -fk https://localhost:8081/ui/get_messages -s)" == "{}" ]; then echo "sickchill is alive"; else echo "sickchill is not responding" && exit 1; fi'
