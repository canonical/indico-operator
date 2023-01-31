#!/bin/bash

set -e

indico db prepare
indico db upgrade
indico db --all-plugins upgrade
uwsgi --ini /etc/uwsgi.ini
