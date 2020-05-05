FROM python:2.7-alpine
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

ARG SICKCHILL_UID=317
ARG SICKCHILL_USER=sickchill

RUN adduser --uid ${SICKCHILL_UID} --disabled-password ${SICKCHILL_USER}

RUN apk add --update --no-cache \
    git mediainfo unrar tzdata libffi openssl \
    && apk add --no-cache --virtual .build-deps \
    gcc libffi-dev openssl-dev musl-dev \
    && pip install pyopenssl \
    && apk del .build-deps gcc \
    &&  mkdir -p /app /var/run/sickchill /data/config  \
    && chown -R ${SICKCHILL_USER}:${SICKCHILL_USER} /var/run/sickchill /data/

USER ${SICKCHILL_USER}

COPY --chown=${SICKCHILL_USER}:${SICKCHILL_USER} . /app/sickchill

WORKDIR /app/sickchill
VOLUME /data /downloads /tv
CMD /usr/local/bin/python SickBeard.py -q --nolaunch --datadir=/data --port 8081
EXPOSE 8081
