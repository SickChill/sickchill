FROM python:3.7-alpine
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v ShowPath:/ShowPath \
# -v DownloadPath:/DownloadPath \
# -v /docker/sickchill/data:/data \
# -v /docker/sickchill/cache/gui:/app/sickchill/sickchill/gui/slick/cache \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

RUN apk add --update --no-cache \
    git mediainfo unrar tzdata libffi openssl \
    && apk add --no-cache --virtual .build-deps \
    gcc libffi-dev openssl-dev musl-dev \
    && pip install pyopenssl \
    && apk del .build-deps gcc \
    &&  mkdir /app /var/run/sickchill

WORKDIR /app/sickchill
VOLUME /data /downloads /tv
COPY . /app/sickchill
RUN chmod -R 777 /app/sickchill
CMD /usr/local/bin/python SickChill.py -q --nolaunch --datadir=/data --port 8081
EXPOSE 8081
