FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update \
    && apt install -y libpq-dev python3-pip \
    && pip install --prefer-binary indico==3.2 indico-plugins

FROM ubuntu:jammy

RUN apt update \
    && apt install -y nginx

COPY --from=0 /usr/local/lib/python3.10/dist-packages/indico/web/static /srv/indico/static
COPY files/etc/nginx/nginx.conf /etc/nginx/nginx.conf

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx \
    && chown -R nginx:nginx /srv/indico/static/ \
    && chmod 755 /srv/indico/static

