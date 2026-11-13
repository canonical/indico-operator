#!/bin/bash
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -euo pipefail
set +x

cd "$(dirname "$0")/../.."

sudo snap install microceph
sudo microceph cluster bootstrap
sudo microceph disk add loop,1G,3
sudo microceph enable rgw --port 7480 --wait

curl --silent --show-error --output /dev/null \
    --connect-timeout 2 --max-time 3 \
    --retry 5 --retry-delay 2 --retry-connrefused \
    http://127.0.0.1:7480

umask 077
mkdir -p build
sudo microceph.radosgw-admin user create \
    --uid indico-test --display-name "Indico integration tests" \
    | tee build/s3-user.json > /dev/null
sudo chown "${SUDO_USER:-$(id -un)}" build/s3-user.json
