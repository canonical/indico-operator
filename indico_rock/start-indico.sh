#!/bin/bash

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

set -e
echo "Preparing DB"
# We can ignore failures here, as this will fail if the DB isn't empty but isn't needed if it is
indico db prepare || true
echo "Upgrading DB"
indico db upgrade
echo "Upgrading plugins"
indico db --all-plugins upgrade
echo "Starting uwsgi"
uwsgi --ini /etc/uwsgi.ini
