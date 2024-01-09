# syntax=docker/dockerfile:experimental

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v mount_point:/mount_point \
# -v /docker/sickchill/data:/data \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

FROM --platform=$TARGETPLATFORM python:3.10-slim-bullseye as base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONUNBUFFERED=1

ARG SOURCE
ARG PIP_EXTRA_INDEX_URL="https://www.piwheels.org/simple"
ARG HOME=${HOME:-}

ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH="$HOME/.venv"
ENV POETRY_CACHE_DIR="$HOME/.cache/pypoetry"
ENV POETRY_HOME="$HOME/.poetry"

ENV PATH=$POETRY_VIRTUALENVS_PATH/local/bin:$POETRY_VIRTUALENVS_PATH/bin:$PATH

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
# ENV SODIUM_INSTALL=system

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL

# TODO: Add a user and drop privileges, preferablty from --user argument

RUN mkdir -m 777 -p /sickchill "$POETRY_CACHE_DIR"

RUN sed -i -e "s/ main/ main contrib non-free/gm" /etc/apt/sources.list
RUN apt-get update -qq && apt-get upgrade -yqq && \
 apt-get install -yqq curl libxml2 libxslt1.1 libffi7 libssl1.1 libmediainfo0v5 mediainfo unrar && \
 apt-get clean -yqq && \
 rm -rf /var/lib/apt/lists/*

FROM base as builder
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
RUN --security=insecure curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sed "s#/proc/self/exe#$SHELL#g" | sh -s -- -y --profile minimal --default-toolchain nightly

ENV PATH "$RUSTUP_HOME/bin:$CARGO_HOME/bin:$PATH"

# Always just create our own virtualenv to prevent issues
RUN python3 -m venv "$POETRY_VIRTUALENVS_PATH" --upgrade --upgrade-deps # upgrade-deps requires python3.9+
RUN pip install -U wheel setuptools-rust

WORKDIR /sickchill
COPY . /sickchill/

# https://github.com/rust-lang/cargo/issues/8719#issuecomment-1253575253
# hadolint ignore=SC2215,SC1089
RUN --mount=type=tmpfs,target="$CARGO_HOME" if [ -z "$SOURCE" ]; then \
  pip install --upgrade "sickchill[speedups]"; \
else \
  pip install --upgrade poetry && poetry run pip install -U setuptools-rust pycparser && \
  poetry build --no-interaction --no-ansi && pip install --upgrade --find-links=./dist "sickchill[speedups]"; \
fi

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

FROM base as sickchill-final

COPY --from=builder "$POETRY_VIRTUALENVS_PATH" "$POETRY_VIRTUALENVS_PATH"

# When you docker exec, show the config files in the container
ENV HOME=/data
WORKDIR /data

VOLUME /data /downloads /tv

CMD ["sickchill", "--nolaunch", "--datadir", "/data", "--port", "8081"]
EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
 CMD bash -c 'if [ $(curl -f http://localhost:8081/ui/get_messages -s) == "{}" ]; then echo "sickchill is alive"; elif [ $(curl -f https://localhost:8081/ui/get_messages -s) == "{}" ]; then echo "sickchill is alive"; else echo 1; fi'
