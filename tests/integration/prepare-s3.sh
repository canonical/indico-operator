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

# MicroCeph's --wait can return before RGW starts accepting HTTP connections.
if ! curl --silent --show-error --output /dev/null \
    --connect-timeout 2 --max-time 3 \
    --retry 60 --retry-delay 2 --retry-max-time 180 --retry-connrefused \
    http://127.0.0.1:7480; then
    echo "MicroCeph RGW did not become ready on port 7480." >&2
    sudo snap logs microceph.rgw -n 100
    exit 1
fi

umask 077
mkdir -p build
sudo microceph.radosgw-admin user create \
    --uid indico-test --display-name "Indico integration tests" \
    | tee build/s3-user.json > /dev/null
sudo chown "${SUDO_USER:-$(id -un)}" build/s3-user.json
