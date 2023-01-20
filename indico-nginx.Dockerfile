FROM ubuntu:jammy as builder

ENV DEBIAN_FRONTEND=noninteractive

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        python3-dev \
        python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --home /srv/indico --disabled-login nginx
USER nginx
RUN python3 -m pip install --no-cache-dir --no-warn-script-location --prefer-binary \
    indico==3.2 \
    indico-plugin-piwik \
    indico-plugin-storage-s3

FROM ubuntu:jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /srv/indico/.local/lib/python3.10/site-packages/indico/web/static /srv/indico/static
COPY files/etc/nginx/nginx.conf /etc/nginx/nginx.conf

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx
