FROM ubuntu:jammy as builder

ENV DEBIAN_FRONTEND=noninteractive

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN apt-get update \
    && apt-get install -y libpq-dev python3-pip \
    && addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --home /srv/indico --disabled-login nginx
USER nginx
RUN python3 -m pip install --no-cache-dir --prefer-binary indico==3.2 indico-plugins

FROM ubuntu:jammy

RUN apt-get update \
    && apt-get install -y nginx

COPY --from=builder /srv/indico/.local/lib/python3.10/site-packages/indico/web/static /srv/indico/static
COPY files/etc/nginx/nginx.conf /etc/nginx/nginx.conf

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx \
    && chown -R nginx:nginx /srv/indico/static/ \
    && chmod 755 /srv/indico/static

