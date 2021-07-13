FROM python:3.9.6-slim

LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v ShowPath:/ShowPath \
# -v DownloadPath:/DownloadPath \
# -v /docker/sickchill/data:/data \
# -v /docker/sickchill/cache/gui:/app/sickchill/sickchill/gui/slick/cache \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

VOLUME /data /downloads /tv
RUN mkdir /app /var/run/sickchill
WORKDIR /app/sickchill
COPY pyproject.toml /app/sickchill
COPY poetry.lock /app/sickchill

RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -qq && apt-get install -yq git libxml2 libxml2-dev libxslt1.1 \
libxslt1-dev libffi6 libffi-dev libssl1.1 libssl-dev python3-dev \
libmediainfo0v5 libmediainfo-dev mediainfo unrar curl build-essential cargo && \
apt-get clean -yqq && rm -rf /var/lib/apt/lists/*

#apk add --update --no-cache --virtual=build-dependencies \
#cargo g++ gcc git libffi-dev libxslt-dev make openssl-dev python3-dev && \
#apk add --update --no-cache libmediainfo libssl1.1 libxslt py3-pip python3 unrar

# Break layer cache, always install poetry and depends.
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache


RUN pip install --pre --upgrade --prefer-binary \
--find-links https://wheel-index.linuxserver.io/alpine/ \
--find-links https://wheel-index.linuxserver.io/ubuntu/ \
poetry pip wheel setuptools virtualenv && \
export PATH="/root/.local/bin:$PATH" && ln -s /usr/bin/python3 /usr/bin/python && \
poetry export --format requirements.txt > requirements.txt && \
python -m virtualenv -p python3.7 .venv && \
.venv/bin/python3 -m pip install --pre --upgrade --prefer-binary \
--find-links https://wheel-index.linuxserver.io/alpine/ \
--find-links https://wheel-index.linuxserver.io/ubuntu/ \
-r requirements.txt && rm requirements.txt

COPY . /app/sickchill
RUN chmod -R 777 /app/sickchill

CMD .venv/bin/python3 SickChill.py -q --nolaunch --datadir=/data --port 8081

EXPOSE 8081

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8081/ || curl -f https://localhost:8081/ || exit 1
