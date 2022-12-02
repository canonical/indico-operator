FROM ubuntu:jammy as builder

ARG indico_gid=2000
ARG indico_uid=2000

RUN apt-get update \
    && apt-get install -y --no-install-recommends libldap2-dev libpq-dev libsasl2-dev libssl-dev libxmlsec1-dev pkg-config python3-pip \
    && rm /var/lib/apt/lists/* \
    && addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico indico

ENV UWSGI_EMBED_PLUGINS=stats_pusher_statsd

USER indico
RUN python3 -m pip install --no-cache-dir --prefer-binary indico==3.2 indico-plugin-piwik indico-plugin-storage-s3 python-ldap python3-saml uwsgi

FROM ubuntu:jammy as target

COPY --from=builder /srv/indico/.local /srv/indico/.local

ARG indico_gid=2000
ARG indico_uid=2000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LC_LANG=C.UTF-8

RUN apt update \
    && apt install -y --no-install-recommends gettext git libxmlsec1-dev locales postgresql-client python3-pip texlive-xetex \
    && rm /var/lib/apt/lists/* \
    && addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico indico \
    && /bin/bash -c "mkdir -p --mode=775 /srv/indico/{archive,cache,custom,etc,log,tmp}" \
    && chown indico:indico /srv/indico  /srv/indico/cache /srv/indico/archive /srv/indico/custom \
    /srv/indico/etc /srv/indico/.local /srv/indico/log /srv/indico/tmp

USER indico
RUN /srv/indico/.local/bin/indico setup create-symlinks /srv/indico

COPY --chown=indico:indico files/start-indico.sh /srv/indico/
COPY --chown=indico:indico files/etc/indico/ /etc/

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico
