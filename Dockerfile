FROM --platform=$TARGETPLATFORM python:3.9-slim as base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONBUFFERED 1

ARG SOURCE
ARG HOME=${HOME:-/}

ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH="$HOME/.venv"
ENV POETRY_CACHE_DIR="$HOME/.cache/pypoetry"
ENV POETRY_HOME="$HOME/.poetry"

#ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV SODIUM_INSTALL=system

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v mount_point:/mount_point \
# -v /docker/sickchill/data:/data \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

# TODO: Add a user and drop privileges, preferablty from --user argument

RUN mkdir -m 777 -p /sickchill $POETRY_CACHE_DIR

RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -qq && apt-get install -yq curl libxml2 libxslt1.1 libffi7 libssl1.1 libmediainfo0v5 mediainfo unrar python3-cffi python3-cryptography python3-nacl python3-pycparser python3-cffi-backend python3-lxml python3-html5lib && \
    apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

FROM base as builder
RUN apt-get update -qq && apt-get install -yq build-essential cargo rustc libxml2-dev libxslt1-dev libffi-dev libssl-dev libmediainfo-dev python3-dev findutils && \
apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

# Always just create our own virtualenv to prevent issues, try using system-site-packages for apt installed packages
RUN python3 -m venv $POETRY_VIRTUALENVS_PATH --system-site-packages --upgrade --upgrade-deps # upgrade-deps requires python3.9+

ENV PATH=$POETRY_VIRTUALENVS_PATH/local/bin:$POETRY_VIRTUALENVS_PATH/bin
ENV PIP_WHEELS="$(pip cache dir)/wheels"
ENV POETRY_WHEELS="$(poetry config cache-dir)/artifacts"
WORKDIR /sickchill
COPY . /sickchill/

RUN if [ -z $SOURCE ]; then \
      pip install --upgrade --prefer-binary sickchill[speedups] --extra-index-url https://www.piwheels.org/simple --find-links https://wheel-index.linuxserver.io/ubuntu/; \
    else  \
      pip install --upgrade --prefer-binary poetry; poetry build --no-interaction --no-ansi; V=$(poetry version --short) && \
      pip install --upgrade --prefer-binary dist/sickchill-${V}-py3-none-any-wheel[speedups] --extra-index-url https://www.piwheels.org/simple --find-links https://wheel-index.linuxserver.io/ubuntu/; \
    fi

RUN mkdir -m 777 /sickchill-wheels && \
    ls $PIP_WHEELS/*/*/*/*/*.whl | sed "/none-any/d" | xargs -I {} cp --update {} /sickchill-wheels/ && \
    ls $POETRY_WHEELS/*/*/*/*/*.whl | sed "/none-any/d" | xargs -I {} cp --update {} /sickchill-wheels/ && \
    pip download sickchill --dest /sickchill-wheels && \
    rm -rf /sickchill-wheels/*none-any.whl && rm -rf /sickchill-wheels/*.gz

RUN if [ -z $SOURCE ]; then \
      rm -rf /sickchill-wheels/sickchill*.whl && cp dist/sickchill*.whl /sickchill-wheels/; \
    fi

FROM scratch AS sickchill-wheels
COPY --from=builder /sickchill-wheels /

FROM base as sickchill-final

COPY --from=builder $POETRY_VIRTUALENVS_PATH $POETRY_VIRTUALENVS_PATH

# When you docker exec, show the config files in the container
ENV HOME=/data
WORKDIR /data

VOLUME /data /downloads /tv

CMD sickchill --nolaunch --datadir=/data --port 8081
EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8081/ || curl -f https://localhost:8081/ || exit 1
