FROM python:3.8-slim
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v ShowPath:/ShowPath \
# -v DownloadPath:/DownloadPath \
# -v /docker/sickchill/data:/data \
# -v /docker/sickchill/cache/gui:/app/sickchill/sickchill/gui/slick/cache \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

RUN mkdir /app /var/run/sickchill
WORKDIR /app/sickchill
VOLUME /data /downloads /tv
COPY . /app/sickchill
RUN chmod -R 777 /app/sickchill

RUN apt-get update &&\
 apt-get install --no-install-recommends -y software-properties-common &&\
 apt-add-repository non-free && apt-get update &&\
 apt-get install --no-install-recommends -y git mediainfo unrar tzdata ca-certificates &&\
 apt-get purge --autoremove software-properties-common -y &&\
 apt-get clean && rm -rf /var/lib/apt/lists/* &&\
 pip install --no-cache-dir -r requirements.txt

CMD /usr/local/bin/python SickChill.py -q --nolaunch --datadir=/data --port 8081
EXPOSE 8081
