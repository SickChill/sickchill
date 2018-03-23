FROM python:2.7.13-alpine

ENV PID_FILE /var/run/sickrage/sickrage.pid
ENV DATA_DIR /data
ENV CONF_DIR /config/
ENV PUID 1000
ENV PGID 1000

RUN addgroup -g ${PGID} sickrage && \
    adduser -u ${PUID} -D -S -G sickrage sickrage

RUN mkdir /var/run/sickrage/ && \
    chown sickrage. /var/run/sickrage/ && \
    mkdir /config/ && \
    chown sickrage. /config && \
    mkdir /data/ && \
    chown sickrage. /data

COPY --chown=sickrage:sickrage . /app/sickrage

USER sickrage

RUN echo -e "[General]\nauto_update = 1" > /config/config.ini

VOLUME ["/config","/data"]

WORKDIR /app/sickrage/

CMD /usr/local/bin/python SickBeard.py -q --nolaunch --pidfile=${PID_FILE} --config=${CONF_DIR}/config.ini --datadir=${DATA_DIR} ${EXTRA_DAEMON_OPTS}

EXPOSE 8081

