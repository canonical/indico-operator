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

RUN python3.9 -m pip install --prefer-binary indico indico-plugins

FROM ubuntu:jammy

ARG nginx_gid=2001
ARG nginx_uid=2001

RUN addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx

RUN apt update \
    && apt install -y nginx

COPY --from=0 /usr/local/lib/python3.9/dist-packages/indico/web/static /srv/indico/static

COPY files/etc/nginx/nginx.conf /etc/nginx/nginx.conf

RUN chown -R nginx:nginx /srv/indico/static/ \
    && chmod 755 /srv/indico/static

