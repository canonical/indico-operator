FROM ubuntu:jammy as builder

ARG indico_gid=2000
ARG indico_uid=2000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libldap2-dev \
        libpq-dev \
        libsasl2-dev \
        libxmlsec1-dev \
        pkg-config \
        python3-dev \
        python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico indico

ENV UWSGI_EMBED_PLUGINS=stats_pusher_statsd

USER indico
RUN python3 -m pip install --no-cache-dir --no-warn-script-location --prefer-binary \
    indico~=3.2 \
    indico-plugin-piwik \
    indico-plugin-storage-s3 \
    python-ldap \
    python3-saml \
    uwsgi

FROM ubuntu:jammy as target

COPY --from=builder /srv/indico/.local /srv/indico/.local

ARG indico_gid=2000
ARG indico_uid=2000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LC_LANG=C.UTF-8
    
RUN exit 
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        dbus \
        dvisvgm \
        fonts-droid-fallback \
        gettext \
        git \
        libc-devtools \
        libglib2.0-data \
        libldap-common \
        libxmlsec1-dev \
        libsasl2-modules \
        lmodern \
        locales \
        postgresql-client \
        publicsuffix \
        python3-dev \
        python3-pip \
        shared-mime-info \
        tex-gyre \
        texlive-fonts-recommended \
        texlive-plain-generic \
        texlive-xetex \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico indico \
    && /bin/bash -c "mkdir -p --mode=775 /srv/indico/{archive,cache,custom,etc,log,tmp}" \
    && /bin/bash -c "chown indico:indico /srv/indico /srv/indico/{archive,cache,custom,etc,log,tmp,.local}"

USER indico
RUN /srv/indico/.local/bin/indico setup create-symlinks /srv/indico

COPY --chown=indico:indico files/start-indico.sh /srv/indico/
COPY --chown=indico:indico files/etc/indico/ /etc/

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico
