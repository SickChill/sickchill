FROM python:3.8-alpine
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v ShowPath:/ShowPath \
# -v DownloadPath:/DownloadPath \
# -v /docker/sickchill/data:/data \
# -v /docker/sickchill/cache/gui:/app/sickchill/sickchill/gui/slick/cache \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

RUN apk add --update --no-cache git mediainfo unrar tzdata curl ca-certificates\
 libffi libffi-dev libxml2 libxml2-dev libxslt libxslt-dev openssl openssl-dev\
 gcc musl-dev python3-dev && apk add --update --no-cache --virtual .build-deps &&\
 mkdir /app /var/run/sickchill

WORKDIR /app/sickchill
VOLUME /data /downloads /tv
COPY requirements.txt /app/sickchill

RUN CRYPTOGRAPHY_DONT_BUILD_RUST=1 pip install --no-cache-dir --no-input -Ur requirements.txt &&\
 apk del .build-deps gcc libffi-dev libxml2-dev libxslt-dev openssl-dev musl-dev python3-dev

COPY . /app/sickchill
RUN chmod -R 777 /app/sickchill

CMD /usr/local/bin/python SickChill.py -q --nolaunch --datadir=/data --port 8081
EXPOSE 8081
