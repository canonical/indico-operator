FROM ubuntu:jammy

ARG indico_gid=2000
ARG indico_uid=2000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LC_LANG=C.UTF-8 \
    UWSGI_EMBED_PLUGINS=stats_pusher_statsd

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git-core \
        libglib2.0-data \
        libldap2-dev \
        libpq-dev \
        libsasl2-dev \
        libxmlsec1-dev \
        pkg-config \
        postgresql-client \
        python3-dev \
        python3-pip \
        shared-mime-info \
        texlive-fonts-recommended \
        texlive-plain-generic \
        texlive-xetex \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico indico

# Add our plugins
COPY --chown=indico:indico plugins /srv/indico/plugins

USER indico
RUN python3 -m pip install --no-cache-dir --no-warn-script-location --prefer-binary \
    indico==3.2.0 \
    indico-plugin-piwik \
    indico-plugin-storage-s3 \
    python3-saml \
    python-ldap \
    /srv/indico/plugins/autocreate \
    uwsgi \
    && /bin/bash -c "mkdir -p --mode=775 /srv/indico/{archive,cache,custom,etc,log,tmp}" \
    && /bin/bash -c "chown indico:indico /srv/indico /srv/indico/{archive,cache,custom,etc,log,tmp,.local}" \
    && /srv/indico/.local/bin/indico setup create-symlinks /srv/indico

COPY --chown=indico:indico files/start-indico.sh /srv/indico/
COPY --chown=indico:indico files/etc/indico/ /etc/

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico
