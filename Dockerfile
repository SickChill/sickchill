FROM --platform=$TARGETPLATFORM python:3.9-slim as base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONBUFFERED 1

#ENV PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple
#ENV PIP_FIND_LINKS=https://wheel-index.linuxserver.io/ubuntu/

ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=true
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH=$HOME/.venv
ENV POETRY_CACHE_DIR=$HOME/.cache/pypoetry
ENV POETRY_HOME=$HOME/.poetry

#ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV SODIUM_INSTALL=system

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v mount_point:/mount_point \
# -v /docker/sickchill/data:/data \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

# TODO: Add a user and drop privileges, preferablty from --user argument

RUN mkdir -m 777 -p /sickchill $HOME/.cache

RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -qq && apt-get install -yq curl libxml2 libxslt1.1 libffi7 libssl1.1 libmediainfo0v5 mediainfo unrar && \
apt-get purge python3-cffi python3-cryptography python3-nacl python3-pycparser python3-cffi-backend -yq && apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

RUN ulimit -n 8192

FROM base as builder
RUN apt-get update -qq && apt-get install -yq build-essential cargo rustc libxml2-dev libxslt1-dev libffi-dev libssl-dev libmediainfo-dev python3-dev && \
apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade --prefer-binary poetry pip wheel setuptools

WORKDIR /sickchill
COPY . /sickchill/

RUN poetry run python3 -m pip  install --upgrade cffi pynacl greenlet pyopenssl cryptography --force-reinstall
RUN poetry install --no-interaction --no-ansi --without dev --with speedups --with root --without experimental --without types

from base as sickchill-final

COPY --from=builder $POETRY_VIRTUALENVS_PATH $POETRY_VIRTUALENVS_PATH

ENV PATH=$POETRY_VIRTUALENVS_PATH/bin:$POETRY_VIRTUALENVS_PATH/local/bin:$PATH
WORKDIR $POETRY_VIRTUALENVS_PATH/local/bin

VOLUME /data /downloads /tv

CMD SickChill --nolaunch --datadir=/data --port 8081
EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8081/ || curl -f https://localhost:8081/ || exit 1
