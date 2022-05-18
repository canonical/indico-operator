FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update \
    && apt install -y python3.9 python3-apt python3.9-dev python3.9-distutils python3-pip texlive-xetex libpq-dev postgresql-client gcc gettext

RUN set -ex \
    && mkdir /tmp/indico-pip \
    && pip install -U pip setuptools \
    && pip download --python-version 2.7 --no-deps -d /tmp/indico-pip indico \
    && unzip /tmp/indico-pip/indico-*.whl -d /opt/ 'indico/web/static/*'


FROM ubuntu:jammy

ARG nginx_gid=2000
ARG nginx_uid=2000

RUN addgroup --gid ${nginx_gid} nginx \
    && adduser --system --gid ${nginx_gid} --uid ${nginx_uid} --no-create-home --disabled-login nginx

RUN apt update \
    && apt install -y nginx

COPY --from=0 /opt/indico/web/static /opt/indico/web/static
COPY etc/nginx/indico.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080