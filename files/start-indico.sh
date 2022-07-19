#!/bin/bash

set -e

/usr/local/bin/indico db prepare
/usr/local/bin/indico db upgrade
/usr/local/bin/indico db --all-plugins upgrade
/usr/local/bin/uwsgi --ini /srv/indico/etc/uwsgi.ini
