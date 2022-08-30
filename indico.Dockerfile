FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LC_LANG=C.UTF-8

RUN apt update \
    && apt install -y cron gettext git libpq-dev libxmlsec1-dev locales pkg-config postgresql-client python3-pip texlive-xetex

RUN pip install --prefer-binary indico indico-plugin-piwik python3-saml uwsgi \
    && /bin/bash -c "mkdir -p --mode=775 /srv/indico/{etc,tmp,log,cache,archive,custom}" \
    && /usr/local/bin/indico setup create-symlinks /srv/indico
    
ARG indico_gid=2000
ARG indico_uid=2000

RUN addgroup --gid ${indico_gid} indico \
    && adduser --system --gid ${indico_gid} --uid ${indico_uid} --home /srv/indico --disabled-login indico \
    &&  echo "* * * * * git -C /srv/indico/custom pull" | crontab -u indico - \
    && /etc/init.d/cron start

COPY --chown=indico:indico files/start-indico.sh /srv/indico/
COPY files/etc/indico/ /etc/

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico \
    && chmod 755 /srv/indico

