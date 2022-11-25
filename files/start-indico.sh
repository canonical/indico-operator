#!/bin/bash

export PATH="$PATH":/srv/indico/.local/bin
indico db prepare
indico db upgrade
indico db --all-plugins upgrade
uwsgi --ini /etc/uwsgi.ini
