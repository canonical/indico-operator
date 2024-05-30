#!/bin/bash

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

set -e
echo "Preparing DB"
# We can ignore failures here, as this will fail if the DB isn't empty but isn't needed if it is
indico db prepare &>> /srv/indico/log/indico.log || true
echo "Upgrading DB"
indico db upgrade &>> /srv/indico/log/indico.log
echo "Upgrading plugins"
indico db --all-plugins upgrade &>> /srv/indico/log/indico.log
echo "Starting uwsgi"
uwsgi --ini /etc/uwsgi.ini
