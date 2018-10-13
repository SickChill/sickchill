FROM python:2.7-alpine

ARG SICKCHILL_VERSION=master

ENV PID_FILE /var/run/sickchill/sickchill.pid
ENV DATA_DIR /data
ENV CONF_DIR /config/
#ENV PUID 1000
#ENV PGID 1000

VOLUME ["/config","/data"]

RUN apk add --update git

#RUN addgroup -g ${PGID} sickchill && \
#    adduser -u ${PUID} -D -S -G sickchill sickchill

RUN git config --global advice.detachedHead false && \
    git clone --quiet https://github.com/SickChill/SickChill/ --branch $SICKCHILL_VERSION --single-branch --depth=1 /app/sickchill

#RUN mkdir /var/run/sickchill/ && \
#    chown sickchill. /var/run/sickchill/ && \
#    mkdir /config/ && \
#    chown sickchill. /config && \
#    mkdir /data/ && \
#    chown sickchill. /data

RUN echo '[General]' > /config/config.ini; if [ "$SICKCHILL_VERSION" = "master" ]; then echo 'auto_update = 1' >> /config/config.ini ; else echo 'auto_update = 0' >> /config/config.ini ; fi

#RUN if [ "$SICKCHILL_VERSION" = "master" ]; then chown -R sickchill. /app/sickchill/ ; fi


#USER sickchill

WORKDIR /app/sickchill/

CMD /usr/local/bin/python SickBeard.py -q --nolaunch --pidfile=${PID_FILE} --config=${CONF_DIR}/config.ini --datadir=${DATA_DIR} ${EXTRA_DAEMON_OPTS}

EXPOSE 8081
