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

RUN pip install --prefer-binary virtualenv \
    && virtualenv --python=/usr/bin/python3.9 ${INDICO_VIRTUALENV} \
    && ${pip} install --prefer-binary --upgrade pip setuptools \
    && ${pip} install --prefer-binary indico indico-plugins

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

