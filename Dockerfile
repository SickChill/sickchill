FROM python:2.7.13-alpine

ARG SICKRAGE_VERSION

ENV PID_FILE /var/run/sickrage/sickrage.pid
ENV DATA_DIR /data
ENV CONF_DIR /config/

RUN apk update ; apk add git
RUN git config --global advice.detachedHead false
RUN git clone --quiet https://github.com/SickRage/SickRage/ --branch $SICKRAGE_VERSION --single-branch --depth=1 /app/sickrage
RUN mkdir /var/run/sickrage/
RUN mkdir /config/ ; echo '[General]' > /config/config.ini; if [ "$SICKRAGE_VERSION" = "master" ]; then echo 'auto_update = 1' >> /config/config.ini ; else echo 'auto_update = 0' >> /config/config.ini ; fi

VOLUME ["/config","/data"]

WORKDIR /app/sickrage/

CMD /usr/local/bin/python SickBeard.py -q --nolaunch --pidfile=${PID_FILE} --config=${CONF_DIR}/config.ini --datadir=${DATA_DIR} ${EXTRA_DAEMON_OPTS}

EXPOSE 8081
