#!/bin/bash

set -e

/usr/local/bin/indico db prepare --force
/usr/local/bin/indico db upgrade
/usr/local/bin/indico db --all-plugins upgrade
/usr/local/bin/uwsgi --ini /etc/uwsgi.ini
