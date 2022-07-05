FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive

# Python 3.9 is the only version supported by indico at the moment (see
# https://github.com/indico/indico/issues/5364). Install from the PPA
# deadsnakes/ppa until this is addressed.
RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y gettext git libpq-dev libxmlsec1-dev pkg-config postgresql-client python3.9 python3.9-dev python3.9-distutils python3-pip texlive-xetex

RUN python3.9 -m pip install --prefer-binary indico indico-plugins python3-saml uwsgi

ARG indico_gid=2000
ARG indico_uid=2000

RUN addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico --disabled-login indico

ENV DEBIAN_FRONTEND=noninteractive \
    INDICO_CONFIG="/srv/indico/etc/indico.conf"

RUN ["/bin/bash", "-c", "mkdir -p --mode=775 /srv/indico/{etc,tmp,log,cache,archive,custom}"]
RUN /usr/local/bin/indico setup create-symlinks /srv/indico \
    && /usr/local/bin/indico setup create-logging-config /etc

COPY files/start-indico.sh /srv/indico/
COPY files/etc/indico/indico.conf /srv/indico/etc/
COPY files/etc/indico/uwsgi.ini /etc/

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico \
    && chmod 755 /srv/indico

