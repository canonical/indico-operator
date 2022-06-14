#!/bin/bash

set -e

/usr/local/bin/indico db prepare
/usr/local/bin/uwsgi --ini /etc/uwsgi.ini
