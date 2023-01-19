#!/bin/bash

set -e

# env > /srv/indico/env
python3 /etc/indico.conf

/usr/local/bin/indico db prepare
/usr/local/bin/indico db upgrade
/usr/local/bin/indico db --all-plugins upgrade
/usr/local/bin/uwsgi --ini /etc/uwsgi.ini

# #!/usr/bin/env bash
# while IFS= read -r -d '' kvname; do
#   k=${kvname%%=*}
#   v=${kvname#*=}
#   printf 'export %q=%q\n' "$k" "$v"
# done </proc/self/environ
