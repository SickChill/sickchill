FROM python:2.7.13-alpine
ARG
ENV SICKRAGE_VERSION v2017.06.05-1
ENV PID_FILE /var/run/sickrage/sickrage.pid
ENV DATA_DIR /data
ENV CONF_DIR /config/

RUN apk update ; apk add git
RUN git config --global advice.detachedHead false
RUN git clone --quiet https://github.com/SickRage/SickRage/ --branch $SICKRAGE_VERSION --single-branch --depth=1 /app/sickrage
RUN mkdir /var/run/sickrage/


VOLUME ["/config","/data"]

#ADD ./start.sh /start.sh
#RUN chmod u+x  /start.sh

WORKDIR /app/sickrage/

CMD /usr/local/bin/python SickBeard.py -q --nolaunch --pidfile=${PID_FILE} --config=${CONF_DIR}/config.ini --datadir=${DATA_DIR} ${EXTRA_DAEMON_OPTS}
### Run with docker run --rm -it -v /docker/sickrage/data:/data -v /docker/sickrage/config:/config -p 8081:8081 sickrage:v2017.06.05-1


EXPOSE 8081
