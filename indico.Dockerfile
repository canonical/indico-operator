FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive

# Python 3.9 is the only version supported by indico at the moment (see
# https://github.com/indico/indico/issues/5364). Install from the PPA
# deadsnakes/ppa until this is addressed.
RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y libpq-dev python3.9 python3.9-dev python3.9-distutils python3-pip


ENV INDICO_VIRTUALENV="/srv/indico/.venv"
ENV pip="${INDICO_VIRTUALENV}/bin/pip"

RUN ["/bin/bash", "-c", "mkdir -p --mode=775 /srv/indico/{etc,tmp,log,cache,archive,custom}"]
RUN pip install virtualenv \
    && virtualenv --python=/usr/bin/python3.9 ${INDICO_VIRTUALENV} \
    && ${pip} install --upgrade pip setuptools \
    && ${pip} install indico indico-plugins uwsgi

FROM ubuntu:jammy

ARG indico_gid=2000
ARG indico_uid=2000

RUN addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico --disabled-login indico

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y gettext postgresql-client python3.9 python3.9-dev texlive-xetex

ENV INDICO_VIRTUALENV="/srv/indico/.venv" INDICO_CONFIG="/srv/indico/etc/indico.conf"

COPY --from=0 /srv/indico /srv/indico

RUN ${INDICO_VIRTUALENV}/bin/indico setup create-symlinks /srv/indico \
    && ${INDICO_VIRTUALENV}/bin/indico setup create-logging-config /etc

COPY files/start-indico.sh /srv/indico/
COPY files/etc/indico/indico.conf /srv/indico/etc/
COPY files/etc/indico/uwsgi.ini /etc/

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico \
    && chmod 755 /srv/indico

