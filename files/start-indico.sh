#!/bin/bash

set -e

/srv/indico/.venv/bin/indico db prepare
/srv/indico/.venv/bin/uwsgi --ini /etc/uwsgi.ini
