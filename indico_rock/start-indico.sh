#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

set -e
set -o pipefail
echo "Preparing DB"
# We can ignore failures here, as this will fail if the DB isn't empty but isn't needed if it is
{ indico db prepare 2>&1 || true; } | tee -a /srv/indico/log/indico.log
echo "Upgrading DB"
indico db upgrade 2>&1 | tee -a /srv/indico/log/indico.log
echo "Upgrading plugins"
indico db --all-plugins upgrade | tee -a /srv/indico/log/indico.log
echo "Starting uwsgi"
uwsgi --ini /etc/uwsgi.ini
