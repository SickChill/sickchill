FROM python:2.7.13-alpine

ARG SICKRAGE_VERSION

ENV PID_FILE /var/run/sickrage/sickrage.pid
ENV DATA_DIR /data
ENV CONF_DIR /config/
ENV PUID 1000
ENV PGID 1000

RUN apk update && \
    apk add git

RUN addgroup -g ${PGID} sickrage && \
    adduser -u ${PUID} -D -S -G sickrage sickrage

RUN git config --global advice.detachedHead false && \
    git clone --quiet https://github.com/Sick-Rage/Sick-Rage/ --branch $SICKRAGE_VERSION --single-branch --depth=1 /app/sickrage

RUN mkdir /var/run/sickrage/ && \
    chown sickrage. /var/run/sickrage/ && \
    mkdir /config/ && \
    chown sickrage. /config && \
    mkdir /data/ && \
    chown sickrage. /data

RUN echo '[General]' > /config/config.ini; if [ "$SICKRAGE_VERSION" = "master" ]; then echo 'auto_update = 1' >> /config/config.ini ; else echo 'auto_update = 0' >> /config/config.ini ; fi

RUN if [ "$SICKRAGE_VERSION" = "master" ]; then chown -R sickrage. /app/sickrage/ ; fi

VOLUME ["/config","/data"]

USER sickrage

WORKDIR /app/sickrage/

CMD /usr/local/bin/python SickBeard.py -q --nolaunch --pidfile=${PID_FILE} --config=${CONF_DIR}/config.ini --datadir=${DATA_DIR} ${EXTRA_DAEMON_OPTS}

EXPOSE 8081
