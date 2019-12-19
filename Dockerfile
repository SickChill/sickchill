FROM python:2.7-alpine
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

# TODO: Handle permissions so data/config isnt owned by root

RUN apk add --update --no-cache \
    git \
    mediainfo \
    nodejs \
    unrar \
    tzdata \
    libffi \
    openssl \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    libffi-dev \
    openssl-dev \
    musl-dev \
    && pip install pyopenssl \
    && apk del .build-deps \
    &&  mkdir /app /var/run/sickchill
COPY . /app/sickchill

WORKDIR /app/sickchill

VOLUME /data /downloads /tv

CMD /usr/local/bin/python SickBeard.py -q --nolaunch --datadir=/data --port 8081

EXPOSE 8081
