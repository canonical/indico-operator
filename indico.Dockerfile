FROM ubuntu:jammy

ARG indico_gid=2000
ARG indico_uid=2000

ENV DEBIAN_FRONTEND=noninteractive

RUN addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /opt/indico --disabled-login indico

RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y python3.9 python3-apt python3.9-dev python3.9-distutils python3-pip texlive-xetex libpq-dev postgresql-client gcc gettext

ENV INDICO_VIRTUALENV="/opt/indico/.venv" INDICO_CONFIG="/opt/indico/etc/indico.conf"
ENV pip="${INDICO_VIRTUALENV}/bin/pip"

RUN ["/bin/bash", "-c", "mkdir -p --mode=775 /opt/indico/{etc,tmp,log,cache,archive,custom}"]
RUN pip install virtualenv \
    && virtualenv --python=/usr/bin/python3.9 ${INDICO_VIRTUALENV} \
    && ${pip} install --upgrade pip setuptools \
    && ${pip} install uwsgi \
    && ${pip} install indico \
    && ${pip} install indico-plugins

RUN ${INDICO_VIRTUALENV}/bin/indico setup create-symlinks /opt/indico \
    && ${INDICO_VIRTUALENV}/bin/indico setup create-logging-config /opt/indico/etc \
    && chgrp -R indico /opt/indico

COPY etc/indico/indico.conf /opt/indico/etc/
COPY etc/indico/uwsgi.ini /etc/

EXPOSE 8081
