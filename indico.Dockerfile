FROM ubuntu:jammy

ARG indico_gid=2000
ARG indico_uid=2000
ARG nginx_gid=2001
ARG nginx_uid=2001

ENV DEBIAN_FRONTEND=noninteractive

RUN addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico --disabled-login indico \
    && addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx

RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y python3.9 python3-apt python3.9-dev python3.9-distutils python3-pip texlive-xetex libpq-dev \
        postgresql-client gcc gettext nginx

ENV INDICO_VIRTUALENV="/srv/indico/.venv" INDICO_CONFIG="/srv/indico/etc/indico.conf"
ENV pip="${INDICO_VIRTUALENV}/bin/pip"

RUN ["/bin/bash", "-c", "mkdir -p --mode=775 /srv/indico/{etc,tmp,log,cache,archive,custom}"]
RUN pip install virtualenv \
    && virtualenv --python=/usr/bin/python3.9 ${INDICO_VIRTUALENV} \
    && ${pip} install --upgrade pip setuptools \
    && ${pip} install uwsgi \
    && ${pip} install indico \
    && ${pip} install indico-plugins

RUN ${INDICO_VIRTUALENV}/bin/indico setup create-symlinks /srv/indico \
    && ${INDICO_VIRTUALENV}/bin/indico setup create-logging-config /etc

COPY files/start-indico.sh /srv/indico/
COPY files/etc/indico/indico.conf /srv/indico/etc/
COPY files/etc/indico/uwsgi.ini /etc/
COPY files/etc/nginx/nginx.conf /etc/nginx/nginx.conf

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico \
    && chown -R nginx:nginx /srv/indico/static/ \
    && chmod 755 /srv/indico

