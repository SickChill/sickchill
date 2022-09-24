FROM --platform=$TARGETPLATFORM python:3.10-slim as base

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"
ENV PYTHONBUFFERED 1

ENV PIP_NO_CACHE_DIR 1
ENV PIP_FIND_LINKS=https://wheel-index.linuxserver.io/ubuntu/

ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH=$HOME/.venv
ENV POETRY_CACHE_DIR=$HOME/.cache/pypoetry
ENV POETRY_HOME=$HOME/.poetry

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v mount_point:/mount_point \
# -v /docker/sickchill/data:/data \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

RUN mkdir -m 777 -p /sickchill $HOME/.cache

RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -qq && apt-get install -yq libxml2 libxslt1.1 libffi7 libffi8 libssl1.1 libmediainfo0v5  mediainfo unrar && \
apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

FROM base as builder 
RUN apt-get update -qq && apt-get install -yq build-essential cargo libxml2-dev libxslt1-dev libffi-dev libssl-dev libmediainfo-dev python3-dev && \
apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade --prefer-binary poetry pip wheel setuptools

WORKDIR /sickchill
COPY . .

RUN poetry install --no-interaction --no-ansi
WORKDIR $POETRY_VIRTUALENVS_PATH/local/bin
RUN rm -rf /sickchill

from base as final
COPY --from=builder $POETRY_VIRTUALENVS_PATH $POETRY_VIRTUALENVS_PATH

VOLUME /data /downloads /tv

CMD SickChill --nolaunch --datadir=/data --port 8081
EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8081/ || curl -f https://localhost:8081/ || exit 1
