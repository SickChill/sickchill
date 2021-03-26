FROM python:3.7-slim-buster
LABEL org.opencontainers.image.source="https://github.com/sickchill/sickchill"
LABEL maintainer="miigotu@gmail.com"
ENV PYTHONIOENCODING="UTF-8"

# docker run -dit --user 1000:1000 --name sickchill --restart=always \
# -v ShowPath:/ShowPath \
# -v DownloadPath:/DownloadPath \
# -v /docker/sickchill/data:/data \
# -v /docker/sickchill/cache/gui:/app/sickchill/sickchill/gui/slick/cache \
# -v /etc/localtime:/etc/localtime:ro
# -p 8080:8081 sickchill/sickchill

VOLUME /data /downloads /tv
RUN mkdir /app /var/run/sickchill
WORKDIR /app/sickchill
COPY requirements.txt /app/sickchill

# Buster default python3-dev is python3.7 headers, do not change base image until default python3-dev changes in buster.
RUN sed -i -e's/ main/ main contrib non-free/gm' /etc/apt/sources.list
RUN apt-get update -q && \
 apt-get install -yq build-essential curl git libssl-dev libffi-dev libxml2 libxml2-dev libxslt1.1 libxslt-dev libz-dev mediainfo python3-dev unrar && \
 pip install -U pip wheel && \
 curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs >> rustup-init.sh && \
 sh rustup-init.sh -y --default-host=$(gcc -dumpmachine | sed 's/-/-unknown-/') && \
 rm rustup-init.sh && \
 PATH=$PATH:$HOME/.cargo/bin pip install --no-cache-dir --no-input -Ur requirements.txt && \
 PATH=$PATH:$HOME/.cargo/bin/rustup self uninstall -y && \
 apt-get purge -yq --autoremove build-essential libssl-dev libffi-dev libxml2-dev libxslt-dev libz-dev python3-dev && \
 apt-get clean -yq && rm -rf /var/lib/apt/lists/*

COPY . /app/sickchill
RUN chmod -R 777 /app/sickchill

CMD /usr/local/bin/python SickChill.py -q --nolaunch --datadir=/data --port 8081
EXPOSE 8081
