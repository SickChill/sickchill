FROM python:3.9-slim as build

ENV PYTHONIOENCODING="UTF-8"
ENV PIP_FIND_LINKS=https://wheel-index.linuxserver.io/ubuntu/
ENV POETRY_INSTALLER_PARALLEL=false
ENV POETRY_VIRTUALENVS_CREATE=true
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v ShowPath:/ShowPath \
# -v DownloadPath:/DownloadPath \
# -v /docker/sickchill/data:/data \
# -v /docker/sickchill/cache/gui:/app/sickchill/sickchill/gui/slick/cache \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

RUN mkdir -p /app/sickchill /var/run/sickchill $HOME/.cache/pip
RUN chmod -R 777 /app/sickchill $HOME/.cache
WORKDIR /app/sickchill

RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -qq && apt-get install -yq git gosu libxml2 libxml2-dev \
libxslt1.1 libxslt1-dev libffi7 libffi-dev libssl1.1 libssl-dev python3-dev \
libmediainfo0v5 libmediainfo-dev mediainfo unrar curl build-essential && \
apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade --prefer-binary poetry pip wheel setuptools && \
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

COPY . /app/sickchill

# Have to chmod again
RUN chmod -R 777 /app/sickchill $HOME/.cache

RUN . $HOME/.cargo/env && poetry install --no-root --no-interaction --no-ansi
# And again
RUN chmod -R 777 /app/sickchill $HOME/.cache

FROM python:3.9-slim
EXPOSE 8081
CMD PIP_NO_CACHE_DIR=true poetry run python3 /app/sickchill/SickChill.py --nolaunch --datadir=/data --port 8081
# TODO see if works without git
LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"
RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list\
    && apt-get update -qq && apt-get install -yq\
    curl\
    git\
    libxml2\
    libxslt1.1\
    libffi7\
    libssl1.1\
    mediainfo\
    unrar\
    && apt-get clean -yqq && rm -rf /var/lib/apt/lists/*\
    && pip3 install --no-cache-dir --upgrade --prefer-binary poetry\
    && (umask 0 && mkdir /data /downloads /tv)
VOLUME /data /downloads /tv
COPY --from=build /app/sickchill /app/sickchill
WORKDIR /app/sickchill

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8081/ || curl -f https://localhost:8081/ || exit 1
