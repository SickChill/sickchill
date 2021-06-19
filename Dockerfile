FROM python:slim-buster
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

RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -q && \
 apt-get install -yq git libxml2 libxslt1.1 mediainfo unrar && \
 pip install --no-cache-dir --no-input -U poetry && \
 poetry install --no-root --no-dev && \
 apt-get clean -yq && rm -rf /var/lib/apt/lists/*

COPY . /app/sickchill
RUN chmod -R 777 /app/sickchill

CMD poetry run python SickChill.py -q --nolaunch --datadir=/data --port 8081
EXPOSE 8081
