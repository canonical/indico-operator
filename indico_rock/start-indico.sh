#!/bin/bash

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

set -e

indico db prepare
indico db upgrade
indico db --all-plugins upgrade
uwsgi --ini /etc/uwsgi.ini
