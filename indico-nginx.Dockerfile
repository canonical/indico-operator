FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive

# Python 3.9 is the only version supported by indico at the moment. Meaning it has to be installed from the PPA
# deadsnakes/ppa
RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y gcc gettext libpq-dev postgresql-client python3.9 python3-apt python3.9-dev python3.9-distutils \
    python3-pip texlive-xetex


ENV INDICO_VIRTUALENV="/srv/indico/.venv" INDICO_CONFIG="/srv/indico/etc/indico.conf"
ENV pip="${INDICO_VIRTUALENV}/bin/pip"

RUN ["/bin/bash", "-c", "mkdir -p --mode=775 /srv/indico/{etc,tmp,log,cache,archive,custom}"]
RUN pip install virtualenv \
    && virtualenv --python=/usr/bin/python3.9 ${INDICO_VIRTUALENV} \
    && ${pip} install --upgrade pip setuptools \
    && ${pip} install indico \
    && ${pip} install indico-plugins


FROM ubuntu:jammy

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update \
    && apt install -y nginx

COPY --from=0 /srv/indico/.venv/lib/python3.9/site-packages/indico/web/static /srv/indico/static

COPY files/etc/nginx/nginx.conf /etc/nginx/nginx.conf

RUN chown -R nginx:nginx /srv/indico/static/ \
    && chmod 755 /srv/indico/static

