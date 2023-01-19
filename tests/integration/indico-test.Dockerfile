ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Add "indico user autocreate" command
COPY --chown=indico:indico tests/integration/files/src/indico/cli/user.py /usr/local/lib/python3.10/dist-packages/indico/cli/user.py

# Hack indico.conf so that we get env values even if the env is not populated
COPY --chown=indico:indico tests/integration/files/etc/indico/indico.conf /etc/indico.conf

COPY --chown=indico:indico tests/integration/files/start-indico.sh /srv/indico/start-indico.sh

RUN chmod +x /srv/indico/start-indico.sh \
    && chown -R indico:indico /srv/indico
